from werkzeug import Request as BaseRequest
from werkzeug.utils import cached_property
from secure_cookie.cookie import SecureCookie

from .locals import current_app


class Request(BaseRequest):
	@cached_property
	def session(self) -> SecureCookie:
		secret_key = current_app.config['SECRET_KEY']
		return SecureCookie.load_cookie(self, secret_key=secret_key)
