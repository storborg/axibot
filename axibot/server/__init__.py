import logging
import os
import os.path

from aiohttp import web
import aiohttp_themes

from . import views
from .themes.light import LightTheme

log = logging.getLogger(__name__)


__here__ = os.path.dirname(os.path.realpath(__file__))


def make_app():
    app = web.Application()

    aiohttp_themes.setup(app,
                         themes=[LightTheme],
                         debug=True,
                         theme_strategy='light',
                         compiled_asset_dir='/tmp/compiled')

    app.router.add_route('GET', '/', views.index)
    app.router.add_route('POST', '/move/{dir}', views.move)
    app.router.add_route('POST', '/start', views.start)

    static_dir = os.path.join(__here__, 'themes', 'light', 'static')
    app.router.add_static('/_light', static_dir)

    return app


def serve(opts):
    app = make_app()
    web.run_app(app, port=opts.port)
