from __future__ import annotations

from wtforms import Form as BaseForm
from wtforms.meta import DefaultMeta
from wtforms.csrf.core import CSRF, CSRFTokenField
from werkzeug.utils import cached_property

from .locals import current_app, d
from .csrf import generate_csrf_token, validate_csrf_token, CSRF_FIELD_NAME, \
	CSRF_MAX_AGE


class FormCSRF(CSRF):
	@staticmethod
	def generate_csrf_token(_: CSRFTokenField):
		return generate_csrf_token()

	@staticmethod
	def validate_csrf_token(_: Form, field: CSRFTokenField) -> None:
		if d.get("csrf_is_valid"):
			# Already validated by `csrf.CSRFProtect`,
			# which is almost always the case.
			return

		validate_csrf_token(field.data)


class Form(BaseForm):
	class Meta(DefaultMeta):
		csrf = True
		csrf_class = FormCSRF
		csrf_field_name = CSRF_FIELD_NAME
		csrf_time_limit = CSRF_MAX_AGE

		@cached_property
		def csrf_secret(self) -> str:
			return current_app.config['SECRET_KEY']
