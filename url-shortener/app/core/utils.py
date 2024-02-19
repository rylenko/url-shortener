from functools import wraps
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Any, List, Tuple, Optional, Callable

from .locals import current_app, request, url_adapter


def is_safe_url(url: str, /) -> bool:
	host_url = urlparse(request.host_url)
	target_url = urlparse(urljoin(request.host_url, url))

	return (target_url.scheme in {"http", "https"}
			and target_url.netloc == host_url.netloc)


def render_template(name: str, /, **context: Any) -> str:
	return current_app.template_lookup.get_template(name).render(**context)


def url_for(
	endpoint: str,
	/,
	*,
	method: Optional[str] = None,
	**values: Any,
) -> str:
	return url_adapter.build(endpoint, method=method, values=values)


def flash(message: str, /, category: str) -> None:
	request.session.setdefault("_flashes", []).append((message, category))


def get_flashed_messages() -> List[Tuple[str, str]]:
	return request.session.pop("_flashes", [])


def strftime(dt: datetime, /) -> str:
	return dt.strftime(current_app.datetime_format)


def make_next_param(url: str, /) -> str:
	"""Used when creating a link for the `?next` parameter,
	to redirect the user after the next view works."""

	parsed_url = urlparse(url)
	return urlunparse((
		"",
		"",
		parsed_url.path,
		parsed_url.params,
		parsed_url.query,
		"",
	))


def get_next_param() -> Optional[str]:
	"""Used to retrieve the link from `?next`, to which the user
	should be redirected when the view has finished its work.

	`?next` parameter can be tampered with, so it is better to use
	this than `request.args.get("next")`."""

	rv = request.args.get("next", type=str)
	return rv if rv is not None and is_safe_url(rv) else None


def make_condition_decorator(
	f: Callable,
	condition: Callable[[], bool],
	otherwise: Callable[[], Optional[Any]],
	*, return_otherwise: bool = False,
) -> Callable:
	"""
	The decorator that checks that `condition()` returns `True`,
	otherwise uses `otherwise()`. Login required decorator example:

		def login_required(decorated_function: Callable) -> Callable:
			return _make_condition_decorator(
				decorated_function,
				lambda: current_user.is_authenticated,
				lambda: abort(401),
		)
	"""

	@wraps(f)
	def wrapper(*args: Any, **kwargs: Any) -> Any:
		if not condition():
			if return_otherwise:
				return otherwise()
			otherwise()
		return f(*args, **kwargs)

	return wrapper
