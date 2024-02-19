import secrets

import sqlalchemy as sa
from werkzeug.security import generate_password_hash, check_password_hash

from .core.db import Model
from .core.auth import UserMixin


class User(UserMixin, Model):
	username \
		= sa.Column(sa.String(30), unique=True, index=True, nullable=False)
	password_hash = sa.Column(sa.String(255))
	is_active = sa.Column(sa.Boolean, default=True)
	is_staff = sa.Column(sa.Boolean, default=False)

	def __repr__(self) -> str:
		return "<User username=\"%s\">" % self.username

	def get_id(self) -> int:
		return self.id

	def set_password(self, password: str, /) -> None:
		self.password_hash = generate_password_hash(password, "sha256")

	def check_password(self, password: str, /) -> bool:
		if self.password_hash is None:
			return False
		return check_password_hash(self.password_hash, password)


class ShortURL(Model):
	owner_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
	owner = sa.orm.relationship("User", backref=sa.orm.backref(
		"short_urls", cascade="all,delete", lazy="dynamic",
	))
	full_url = sa.Column(sa.Text, index=True, nullable=False)
	clicks = sa.Column(sa.Integer, nullable=False, default=0)
	slug = sa.Column(sa.String(4), unique=True, index=True,
 					nullable=False, default=lambda: secrets.token_hex(2))

	def __repr__(self) -> str:
		return "<ShortURL slug=\"%s\" clicks=%d>" % (self.slug, self.clicks)
