from __future__ import annotations

import os
from hashlib import sha1
from urllib.parse import urlparse

from werkzeug.security import safe_str_cmp
from werkzeug.exceptions import BadRequest
from wtforms.validators import ValidationError
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer

from .locals import current_app, request, d


CSRF_MAX_AGE = 3600
CSRF_SALT = "csrf-token"
CSRF_FIELD_NAME = "csrf_token"
CSRF_REQUEST_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def generate_csrf_token() -> str:
	"""First it generates a raw token by placing it in
	the `request.session` object, then signs the raw token
	for placement in the form and puts it in the local `d`
	dictionary."""

	if CSRF_FIELD_NAME not in d:
		serializer = URLSafeTimedSerializer(
			current_app.config['SECRET_KEY'],
			salt=CSRF_SALT,
		)

		if CSRF_FIELD_NAME not in request.session:
			request.session[CSRF_FIELD_NAME] = sha1(os.urandom(64)).hexdigest()

		d[CSRF_FIELD_NAME] = serializer.dumps(request.session[CSRF_FIELD_NAME])

	return d[CSRF_FIELD_NAME]


def validate_csrf_token(token: str, /) -> None:
	if not token:
		raise ValidationError("The CSRF token is missing.")
	elif CSRF_FIELD_NAME not in request.session:
		raise ValidationError("The CSRF session token is missing.")

	serializer = URLSafeTimedSerializer(
		current_app.config['SECRET_KEY'],
		salt=CSRF_SALT,
	)

	try:
		raw_token = serializer.loads(token, max_age=CSRF_MAX_AGE)
	except SignatureExpired as exc:
		raise ValidationError("The CSRF token has expired.") from exc
	except BadData as exc:
		raise ValidationError("The CSRF token is invalid.") from exc

	if not safe_str_cmp(request.session[CSRF_FIELD_NAME], raw_token):
		raise ValidationError("The CSRF tokens do not match.")


class CSRFError(BadRequest):
	description = "CSRF validation failed."


class CSRFProtect:
	"""Checks `CSRF` when the current request method is in
	`CSRF_REQUEST_METHODS`. This comes in handy when we have a form with just
	one button, which eliminates the option of creating an entire class. But
	at the same time we want to have `CSRF` checking.

	:param app: `core.app.Application` instance.
	"""

	def __init__(self, app, /) -> None:
		app.run_before_request(self.protect)

	@staticmethod
	def _check_same_origin() -> bool:
		host = urlparse("https://%s/" % request.host)
		referrer = urlparse(request.referrer)

		return (
			host.scheme == referrer.scheme
			and host.hostname == referrer.hostname
			and host.port == referrer.port
		)

	def protect(self) -> None:
		if request.method not in CSRF_REQUEST_METHODS:
			return

		try:
			validate_csrf_token(request.form.get(CSRF_FIELD_NAME))
		except ValidationError as exc:
			raise CSRFError(exc.args[0])

		if request.is_secure:
			if not request.referrer:
				raise CSRFError("The referrer header is missing.")

			if not self._check_same_origin():
				raise CSRFError("The referrer does not match the host.")

		d['csrf_is_valid'] = True  # The signal for `forms.FormCSRF`
