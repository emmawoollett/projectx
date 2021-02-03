"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter

from projectx.routing import websocket_urlpatterns

from django.core.asgi import get_asgi_application  # noqa isort:skip
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectx.settings")  # noqa
django_asgi_app = get_asgi_application()  # noqa


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket":  AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    "channel": ChannelNameRouter({
        # "channel_namee": AConsumer(),
    }),
})
