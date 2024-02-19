import sys
import logging
import logging.config
from pathlib import Path
from typing import List, Tuple

import sqlalchemy as sa
from alembic import context
from alembic.operations.ops import MigrationScript
from alembic.runtime.migration import MigrationContext

from app.app import create_app
from app.core.db import Model


app = create_app()
config = context.config
config.set_main_option("sqlalchemy.url", str(
	app.database_manager.engine.url,
))

logger = logging.getLogger("alembic.env")
logging.config.fileConfig(config.config_file_name)

target_metadata = Model.metadata  # type: ignore


def _process_revision_directives(
	context: MigrationContext, revision: Tuple[str],
	directives: List[MigrationScript],
) -> None:
	"""This callback is used to prevent an auto-migration from being
	generated when there are no changes to the schema.

	Reference: https://alembic.zzzcomputing.com/en/latest/cookbook.html"""

	if getattr(config.cmd_opts, 'autogenerate', False):
		script = directives[0]

		if script.upgrade_ops.is_empty():
			directives[:] = []
			logger.info('No changes in schema detected.')


def run_migrations_offline():
	"""Run migrations in 'offline' mode.
	This configures the context with just a URL
	and not an Engine, though an Engine is acceptable
	here as well.  By skipping the Engine creation
	we don't even need a DBAPI to be available.
	Calls to context.execute() here emit the given string to the
	script output.
	"""
	url = config.get_main_option("sqlalchemy.url")
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={"paramstyle": "named"},
	)

	with context.begin_transaction():
		context.run_migrations()


def run_migrations_online():
	"""Run migrations in 'online' mode.
	In this scenario we need to create an Engine
	and associate a connection with the context.
	"""
	connectable = sa.engine.engine_from_config(
		config.get_section(config.config_ini_section),
		prefix="sqlalchemy.",
		poolclass=sa.pool.NullPool,
	)

	with connectable.connect() as connection:
		context.configure(
			connection=connection,
			target_metadata=target_metadata,
			process_revision_directives=_process_revision_directives,
		)

		with context.begin_transaction():
			context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()
