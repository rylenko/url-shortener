from typing import Optional

from wtforms.validators import ValidationError

from . import fields
from .models import User, ShortURL
from .core.db import session
from .core.forms import Form
from .core.locals import current_user


class LoginForm(Form):
	username = fields.UsernameField()
	password = fields.PasswordField()
	submit = fields.SubmitField()

	requested_user: Optional[User] = None

	def validate(self) -> bool:
		self.requested_user = User.query.filter_by(
			username=self.username.data, is_active=True,
		).first()

		return super().validate()

	def validate_submit(self, field: fields.SubmitField) -> None:
		if not (
			self.requested_user is not None
			and self.requested_user.check_password(self.password.data)
		):
			raise ValidationError("Invalid username or password.")


class RegisterForm(Form):
	username = fields.UsernameField()
	password = fields.PasswordField()
	password_confirm = fields.PasswordConfirmField()
	submit = fields.SubmitField()

	def populate(self) -> User:
		rv = User(username=self.username.data)  # type: ignore
		rv.set_password(self.password.data)
		session.add(rv)

		return rv

	def validate_username(self, field: fields.UsernameField) -> None:
		if User.query.filter_by(username=field.data).first() is not None:
			raise ValidationError("A user with this name already exists.")


class DeactivateForm(Form):
	password = fields.PasswordField()
	submit = fields.SubmitField(render_kw={
		'value': "Deactivate!",
		'class': "btn btn-danger",
	})

	def validate_password(self, field: fields.PasswordField) -> None:
		if not current_user.check_password(field.data):
			raise ValidationError("Invalid password.")


class ShortURLForm(Form):
	full_url = fields.FullURLField()
	submit = fields.SubmitField()

	def populate(self) -> ShortURL:
		rv = ShortURL(  # type: ignore
			owner=current_user,
			full_url=self.full_url.data,
		)
		session.add(rv)
		return rv
