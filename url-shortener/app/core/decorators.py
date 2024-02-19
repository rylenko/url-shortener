from typing import Callable

from werkzeug.utils import redirect
from werkzeug.exceptions import abort

from .app import ViewType, Response
from .locals import request, current_app, current_user
from .utils import flash, url_for, make_next_param, make_condition_decorator


def _unauthorized_handler() -> Response:
	endpoint = current_app.login_view_endpoint
	if endpoint is None:
		abort(401)

	flash("Login required.", "danger")
	next_param = make_next_param(request.url)
	return redirect(url_for(endpoint, next=next_param))


def login_required(f: ViewType) -> Callable:
	return make_condition_decorator(
		f, lambda: current_user.is_authenticated,
		_unauthorized_handler, return_otherwise=True,
	)
