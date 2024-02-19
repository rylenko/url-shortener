from typing import Union

from werkzeug.utils import redirect
from werkzeug.exceptions import abort, NotFound, MethodNotAllowed

from .models import ShortURL
from .forms import ShortURLForm
from .decorators import logout_required
from .core.db import session
from .core.app import Response
from .core.decorators import login_required
from .core.locals import current_app, request, current_user
from .core.utils import flash, url_for, render_template, get_next_param

from .forms import LoginForm, RegisterForm, DeactivateForm


def index() -> str:
	return render_template("index.html")


@login_required
def profile() -> str:
	return render_template("accounts/profile.html")


@logout_required
def login() -> Union[str, Response]:
	if request.method == "POST":
		bound_form = LoginForm(request.form)

		if bound_form.validate():
			current_app.login_manager.login_user(bound_form.requested_user)
			flash("You have successfully logged into your account.", "success")
			return redirect(get_next_param() or url_for("profile"))

		return render_template("accounts/login.html", form=bound_form)

	return render_template("accounts/login.html", form=LoginForm())


@logout_required
def register() -> Union[str, Response]:
	if request.method == "POST":
		bound_form = RegisterForm(request.form)

		if bound_form.validate():
			new_user = bound_form.populate()
			session.commit()

			current_app.login_manager.login_user(new_user)
			flash("You have successfully registered your account.", "success")
			return redirect(url_for("profile"))

		return render_template("accounts/register.html", form=bound_form)

	return render_template("accounts/register.html", form=RegisterForm())


@login_required
def logout() -> Response:
	current_app.login_manager.logout_user()
	flash("You have successfully logged out from your account.", "success")
	return redirect(url_for("index"))


@login_required
def deactivate() -> Union[str, Response]:
	if request.method == "POST":
		bound_form = DeactivateForm(request.form)

		if bound_form.validate():
			current_user.is_active = False  # type: ignore
			session.commit()

			current_app.login_manager.logout_user()
			flash("Your account has been deactivated.", "danger")
			return redirect(url_for("index"))

		return render_template("accounts/deactivate.html", form=bound_form)

	return render_template("accounts/deactivate.html", form=DeactivateForm())


@login_required
def list() -> str:
	current_page = current_user.short_urls \
		.order_by(ShortURL.created_at.desc()) \
		.paginate(current_app.config['SHORT_URLS_PER_PAGE'])
	return render_template("short-urls/list.html", current_page=current_page)


@login_required
def create() -> Union[str, Response]:
	if request.method == "POST":
		bound_form = ShortURLForm(request.form)

		if bound_form.validate():
			bound_form.populate()
			session.commit()

			flash("New shortened URL created successfully.", "success")
			return redirect(url_for("list"))

		return render_template("short-urls/create.html", form=bound_form)

	return render_template("short-urls/create.html", form=ShortURLForm())


def follow(slug: str) -> Response:
	short_url = ShortURL.query.filter_by(slug=slug).first_or_404()
	short_url.clicks += 1
	session.commit()

	return redirect(short_url.full_url)


@login_required
def delete(slug: str) -> Union[str, Response]:
	short_url = ShortURL.query.filter_by(slug=slug).first_or_404()

	if short_url.owner != current_user and not current_user.is_staff:
		abort(404)

	if request.method == "POST":
		session.delete(short_url)
		session.commit()

		flash("Your short URL was deleted successfully", "success")
		return redirect(url_for("list"))

	return render_template("short-urls/delete.html", short_url=short_url)


def notfound_handler(_: NotFound) -> Response:
	content = render_template("exceptions/404.html")
	return current_app.make_response(content, 404)


def method_not_allowed_handler(_: MethodNotAllowed) -> Response:
	content = render_template("exceptions/405.html")
	return current_app.make_response(content, 405)
