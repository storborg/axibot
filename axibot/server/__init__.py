import logging
import os
import os.path

from aiohttp import web
import aiohttp_mako

from ..ebb import EiBotBoard, MockEiBotBoard
from .. import planning, config

from . import views, handlers, plotting
from .state import State

log = logging.getLogger(__name__)


__here__ = os.path.dirname(os.path.realpath(__file__))
template_dir = os.path.join(__here__, 'templates')
static_dir = os.path.join(__here__, 'dist')

base_dir = os.path.dirname(os.path.dirname(__here__))
examples_dir = os.path.join(base_dir, 'examples')


def make_app(bot):
    app = web.Application()

    app['state'] = State.idle
    app['action_index'] = 0
    app['clients'] = set()
    app['bot'] = bot
    app['position'] = 0, 0
    app['pen_up'] = None

    bot.enable_motors(1)
    bot.servo_setup(config.PEN_DOWN_POSITION, config.PEN_UP_POSITION,
                    config.SERVO_SPEED, config.SERVO_SPEED)

    app['pen_up_delay'], app['pen_down_delay'] = \
        planning.calculate_pen_delays(config.PEN_UP_POSITION,
                                      config.PEN_DOWN_POSITION,
                                      config.SERVO_SPEED)

    # This will initialize the server state.
    filename = 'line.svg'
    with open(os.path.join(examples_dir, filename)) as f:
        doc = f.read()
        app['job'] = job = plotting.process_upload(app, doc, filename)
        app['estimated_time'] = job.duration().total_seconds()
        app['consumed_time'] = 0

    aiohttp_mako.setup(app,
                       directories=[template_dir],
                       input_encoding='utf-8',
                       output_encoding='utf-8',
                       imports=['from markupsafe import escape'],
                       default_filters=['escape'])

    app.router.add_route('GET', '/', views.index)
    app.router.add_route('GET', '/api', handlers.client_handler)

    app.router.add_static('/static', static_dir)

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
