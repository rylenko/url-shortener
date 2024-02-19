from werkzeug.local import Local, LocalProxy, LocalManager


local = Local()
local_manager = LocalManager([local])

current_app = local("current_app")
request = local("request")
url_adapter = local("url_adapter")
d = local("d")

current_user = LocalProxy(lambda: current_app.login_manager.get_user())
