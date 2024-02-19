from typing import Callable

from werkzeug.utils import redirect

from .core.app import ViewType
from .core.locals import current_user
from .core.utils import make_condition_decorator, url_for


def logout_required(f: ViewType) -> Callable:
	return make_condition_decorator(
		f, lambda: not current_user.is_authenticated,
		lambda: redirect(url_for("profile")),
		return_otherwise=True,
	)
