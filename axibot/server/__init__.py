import logging
import os
import os.path

from aiohttp import web
import aiohttp_themes

from ..ebb import EiBotBoard, MockEiBotBoard

from . import views, handlers, plotting
from .state import State
from .themes.light import LightTheme

log = logging.getLogger(__name__)


__here__ = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.dirname(os.path.dirname(__here__))
examples_dir = os.path.join(base_dir, 'examples')


def make_app(bot):
    app = web.Application()

    app['action_index'] = 0
    app['clients'] = set()
    app['bot'] = bot

    # This will initialize the server state.
    with open(os.path.join(examples_dir, 'rectangles.svg')) as f:
        plotting.set_document(app, f)

    aiohttp_themes.setup(app,
                         themes=[LightTheme],
                         debug=True,
                         theme_strategy='light',
                         compiled_asset_dir='/tmp/compiled')

    app.router.add_route('GET', '/', views.index)
    app.router.add_route('GET', '/document.svg', views.document)
    app.router.add_route('POST', '/upload', views.upload)
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
