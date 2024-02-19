from __future__ import annotations

from functools import wraps
from collections.abc import Mapping
from typing import Any, Dict, List, Type, Union, Tuple, Optional, Callable, \
	Iterator, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
	from sys import _OptExcInfo

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.shared_data import SharedDataMiddleware
from mako.lookup import TemplateLookup

from .csrf import CSRFProtect
from .wrappers import Request
from .db import DatabaseManager
from .auth import LoginManager, UserLoaderType
from .locals import local, local_manager, request, url_adapter


ViewType: TypeAlias = Callable[..., Union[str, Response]]
BeforeRequestFuncType: TypeAlias = Callable[[], Optional[Union[str, Response]]]
ExceptionHandlerType: TypeAlias = Callable[[Exception], Response]
StartResponseType: TypeAlias = Callable[
	[str, List[Tuple[str, str]], Optional[_OptExcInfo]],
	Callable[[bytes], Any],
]


def setup_method(f: Callable) -> Callable:
	"""This is to avoid accidental use of methods like `_apply_middlewares`
	when the application is already processing user requests."""

	@wraps(f)
	def wrapper(self: Application, *args: Any, **kwargs: Any) -> Any:
		assert not self._got_first_request, (
			"Launched after the start of the first request."
		)
		return f(self, *args, **kwargs)

	return wrapper


class Application:
	request_class = Request
	response_class = Response
	csrf_protect_class = CSRFProtect
	database_manager_class = DatabaseManager
	login_manager_class = LoginManager

	datetime_format = "%d.%m.%Y %H:%M:%S"
	template_imports = set((
		"from app.core.locals import current_app",
		"from app.core.locals import request",
		"from app.core.locals import current_user",
		"from app.core.csrf import generate_csrf_token",
		"from app.core.utils import url_for",
		"from app.core.utils import strftime",
		"from app.core.utils import get_flashed_messages",
	))

	config_required_fields = frozenset((
		"SECRET_KEY",
		"TEMPLATES_DIR",
		"TEMPLATES_CACHE_DIR",
		"STATIC_DIR",
	))

	def __init__(
		self,
		config: Mapping[str, Any],
		/,
		user_loader: UserLoaderType,
		*,
		login_view_endpoint: Optional[str] = None,
		static_root: str = "/static/",
	) -> None:
		self.validate_config(config)

		self.config = config
		self.static_root = static_root
		self.login_view_endpoint = login_view_endpoint

		self._views: Dict[str, ViewType] = {}
		self._exception_handlers: \
			Dict[Type[Exception], ExceptionHandlerType] = {}
		self._before_request_funcs: List[BeforeRequestFuncType] = []
		self._got_first_request = False

		self.url_map = Map()
		self.template_lookup = TemplateLookup(
			directories=[config['TEMPLATES_DIR']],
			module_directory=config['TEMPLATES_CACHE_DIR'],
			imports=self.template_imports,
		)

		self.csrf_protect = self.csrf_protect_class(self)
		self.login_manager = self.login_manager_class(user_loader)

		database_uri = config.get("DATABASE_URI")
		self.database_manager = (None if database_uri is None else
 								self.database_manager_class(database_uri))

		self._apply_middlewares()

	def __call__(self, environ: Dict[str, Any],
 				start_response: StartResponseType) -> Iterator[bytes]:
		return self.wsgi_app(environ, start_response)

	@classmethod
	def validate_config(cls, config: Mapping[str, Any], /) -> None:
		for field in cls.config_required_fields:
			if field not in config:
				raise ValueError(
					f"Config doesn't contain the required field \"{field}\".",
				)

	@classmethod
	def make_response(cls, content: str, status: int = 200,
  					mimetype: str = "text/html") -> Response:
		return cls.response_class(content, status, mimetype=mimetype)

	@setup_method
	def _apply_middlewares(self) -> None:
		self.wsgi_app = local_manager.make_middleware(  # type: ignore
			self.wsgi_app,
		)
		self.wsgi_app = SharedDataMiddleware(self.wsgi_app, {  # type: ignore
			self.static_root: str(self.config['STATIC_DIR']),
		})

	def _set_locals(self, environ: Dict[str, Any]) -> None:
		local.current_app = self
		local.request = self.request_class(environ)
		local.url_adapter = self.url_map.bind_to_environ(environ)
		local.d = {}

	def run_before_request_funcs(self) -> Optional[Union[str, Response]]:
		for f in self._before_request_funcs:
			rv = f()
			if rv is not None:
				return rv
		return None

	def run_current_view(self) -> Union[str, Response]:
		endpoint, values = url_adapter.match()
		return self._views[endpoint](**values)

	def handle_exception(self, exc: Exception, /) -> Union[str, Response]:
		handler = self._exception_handlers.get(exc.__class__)

		if handler is not None:
			return handler(exc)
		elif isinstance(exc, HTTPException):
			return exc.get_response()
		raise exc

	def finalize_request(self, response: Union[str, Response], /) -> Response:
		if isinstance(response, str):
			response = self.make_response(response)
		elif not isinstance(response, self.response_class):
			raise TypeError("The function didn't return a valid response.")

		request.session.save_cookie(response)
		return response

	def dispatch_request(self) -> Response:
		try:
			response = self.run_before_request_funcs()
			if response is None:
				response = self.run_current_view()
		except Exception as exc:
			response = self.handle_exception(exc)

		return self.finalize_request(response)

	def wsgi_app(
		self,
		environ: Dict[str, Any],
		start_response: StartResponseType,
	) -> Iterator[bytes]:
		self._got_first_request = True
		self._set_locals(environ)

		response = self.dispatch_request()
		return response(environ, start_response)

	@setup_method
	def add_url_rule(
		self,
		rule: str,
		view: ViewType,
		*,
		methods: Tuple[str, ...] = ("GET",),
	) -> None:
		endpoint = view.__name__
		self.url_map.add(Rule(rule, endpoint=endpoint, methods=methods))
		self._views[endpoint] = view

	@setup_method
	def add_exception_handler(
		self,
		exception: Type[Exception],
		handler: ExceptionHandlerType,
	) -> None:
		self._exception_handlers[exception] = handler

	@setup_method
	def run_before_request(self, f: BeforeRequestFuncType, /) -> None:
		self._before_request_funcs.append(f)
