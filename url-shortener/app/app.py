import os
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.exceptions import NotFound, MethodNotAllowed

from . import views
from .models import User
from .core.app import Application


_base_dir = Path(__file__).resolve().parent
_templates_dir = _base_dir.joinpath("templates")

load_dotenv(_base_dir.parent.joinpath(".env"))


def _get_postgresql_database_uri() -> str:
	user = os.environ['POSTGRES_USER']
	password = os.environ['POSTGRES_PASSWORD']
	db = os.environ['POSTGRES_DB']

	return f"postgresql://{user}:{password}@db:5432/{db}"


config = {
	'SECRET_KEY': os.environ['SECRET_KEY'],
	'DATABASE_URI': _get_postgresql_database_uri(),

	'BASE_DIR': _base_dir,
	'STATIC_DIR': _base_dir.joinpath("static"),
	'TEMPLATES_DIR': _templates_dir,
	'TEMPLATES_CACHE_DIR': _templates_dir.joinpath("_cache"),

	'SHORT_URLS_PER_PAGE': 5,
}


def create_app() -> Application:
	app = Application(config, lambda id: User.query.get(id),
  					login_view_endpoint=views.login.__name__)

	app.add_url_rule(
		"/",
		views.index,
	)

	app.add_url_rule(
		"/accounts/profile/",
		views.profile,
	)
	app.add_url_rule(
		"/accounts/login/",
		views.login,
		methods=("GET", "POST"),
	)
	app.add_url_rule(
		"/accounts/register/",
		views.register,
		methods=("GET", "POST"),
	)
	app.add_url_rule(
		"/accounts/logout/",
		views.logout,
	)
	app.add_url_rule(
		"/accounts/deactivate/",
		views.deactivate,
		methods=("GET", "POST"),
	)

	app.add_url_rule(
		"/s/",
		views.list,
	)
	app.add_url_rule(
		"/s/create/",
		views.create,
		methods=("GET", "POST"),
	)
	app.add_url_rule(
		"/s/<string:slug>/",
		views.follow,
	)
	app.add_url_rule(
		"/s/<string:slug>/delete/",
		views.delete,
		methods=("GET", "POST"),
	)

	app.add_exception_handler(
		NotFound,
		views.notfound_handler,
	)
	app.add_exception_handler(
		MethodNotAllowed,
		views.method_not_allowed_handler,
	)

	return app
