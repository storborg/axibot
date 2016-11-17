import logging
import os
import os.path

from aiohttp import web
import aiohttp_themes

from ..ebb import EiBotBoard, MockEiBotBoard

from . import views, handlers
from .state import State
from .themes.light import LightTheme

log = logging.getLogger(__name__)


__here__ = os.path.dirname(os.path.realpath(__file__))


def make_app(bot):
    app = web.Application()

    app['state'] = State.idle_empty
    app['document'] = None
    app['actions'] = []
    app['action_index'] = 0

    app['clients'] = set()
    app['bot'] = bot

    aiohttp_themes.setup(app,
                         themes=[LightTheme],
                         debug=True,
                         theme_strategy='light',
                         compiled_asset_dir='/tmp/compiled')

    app.router.add_route('GET', '/', views.index)
    app.router.add_route('GET', '/document.svg', views.document)
    app.router.add_route('GET', '/api', handlers.client_handler)

    static_dir = os.path.join(__here__, 'themes', 'light', 'static')
    app.router.add_static('/_light', static_dir)

    return app


def serve(opts):
    if opts.mock:
        bot = MockEiBotBoard()
    else:
        bot = EiBotBoard.find()

    try:
        app = make_app(bot)
        web.run_app(app, port=opts.port)
    finally:
        bot.close()
