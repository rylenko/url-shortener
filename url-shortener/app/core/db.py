from __future__ import annotations

from math import ceil
from typing import List
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr, as_declarative
from werkzeug.exceptions import abort

from .locals import request


class Query(sa.orm.Query):
	def get_or_404(self, id: int) -> Model:
		rv = self.get(id)
		if rv is None:
			abort(404)
		return rv

	def first_or_404(self) -> Model:
		rv = self.first()
		if rv is None:
			abort(404)
		return rv

	def paginate(self, per_page: int) -> Pagination:
		if per_page < 1:
			raise ValueError("There must be at least one object per page.")

		current_page_number \
			= request.args.get("page", 1, type=int) if request else 1
		if current_page_number < 1:
			abort(404)

		offset = (current_page_number - 1) * per_page
		items = self.limit(per_page).offset(offset).all()
		# On the first page, if there are no objects,
		# we can place a corresponding inscription.
		if not items and current_page_number > 1:
			abort(404)

		pages_count = ceil(self.count() / per_page)
		return Pagination(current_page_number, pages_count, items)


session = sa.orm.scoped_session(
	sa.orm.sessionmaker(query_cls=Query),
)


@as_declarative()
class Model:
	id = sa.Column(sa.Integer, primary_key=True)
	created_at = sa.Column(sa.DateTime, default=sa.func.now())
	updated_at = sa.Column(sa.DateTime, onupdate=sa.func.now())

	query = session.query_property(query_cls=Query)

	@declared_attr
	def __tablename__(cls) -> str:
		return cls.__name__.lower()  # type: ignore

	def __repr__(self) -> str:
		return '<%s id=%d>' % (self.__class__.__name__, self.id)


class DatabaseManager:
	"""The main goal is to create a database engine and bind it to
	the session and metadata of the base model. `.create_tables` and
	`.drop_tables` are also here because they depend on the engine."""

	def __init__(self, uri: str, /) -> None:
		self.engine = sa.create_engine(uri)
		session.configure(bind=self.engine)
		Model.metadata.bind = self.engine  # type: ignore

	def create_tables(self) -> None:
		Model.metadata.create_all()  # type: ignore

	def drop_tables(self) -> None:
		Model.metadata.drop_all()  # type: ignore


@dataclass
class Pagination:
	current_page_number: int
	pages_count: int
	items: List[Model]

	@property
	def has_next_page(self) -> bool:
		return self.current_page_number < self.pages_count

	@property
	def has_previous_page(self) -> bool:
		return self.current_page_number > 1

	@property
	def next_page_number(self) -> int:
		assert self.has_next_page
		return self.current_page_number + 1

	@property
	def previous_page_number(self) -> int:
		assert self.has_previous_page
		return self.current_page_number - 1
