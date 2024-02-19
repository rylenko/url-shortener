from typing import Union, Callable, Optional

from .locals import request


class UserMixin:
	@property
	def is_authenticated(self) -> bool:
		return True

	def get_id(self) -> int:
		try:
			return self.id  # type: ignore
		except AttributeError as exc:
			raise NotImplementedError(
				"No `id` attribute. Please, override `get_id`.",
			) from exc


UserLoaderType = Callable[[int], Optional[UserMixin]]


class AnonymousUser:
	@property
	def is_authenticated(self) -> bool:
		return False


class LoginManager:
	"""A class with which you can manage user authentication with sessions.

	If you don't understand what `current_user`, `request._user`
	and `get_user` are about:

	The `current_user` is a `werkzeug.local.LocalProxy` to the `get_user`
	method. That is, every time you access `current_user`, it calls `get_user`.
	Accordingly, to avoid loading the user from the session into `get_user`
	every time, we put the original user or `AnonymousUser` object into
	`request._user`.
	"""

	anonymous_user_class = AnonymousUser

	def __init__(self, user_loader: UserLoaderType) -> None:
		self.user_loader = user_loader

	@classmethod
	def _update_request_with_user(cls, user: Optional[UserMixin], /) -> None:
		request._user = cls.anonymous_user_class() if user is None else user

	def _load_user(self) -> None:
		user_id = request.session.get("_user_id")
		user = None if user_id is None else self.user_loader(user_id)
		self._update_request_with_user(user)

	def login_user(self, user: UserMixin, /) -> None:
		request.session['_user_id'] = user.get_id()
		self._update_request_with_user(user)

	def logout_user(self) -> None:
		del request.session['_user_id']
		self._update_request_with_user(None)

	def get_user(self) -> Union[UserMixin, AnonymousUser]:
		if not hasattr(request, "_user"):
			self._load_user()
		return request._user
