from aiohttp import web
import aiohttp_mako
import logging
import os
import os.path

from . import views

log = logging.getLogger(__name__)


FILE_PATH = os.path.dirname(os.path.realpath(__file__))

def make_app(argv):
    app = web.Application()

    lookup = aiohttp_mako.setup(app, input_encoding='utf-8',
                                output_encoding='utf-8',
                                default_filters=['decode.utf8'],
                                directories=[os.path.join(FILE_PATH,"templates")])


    app.router.add_route('GET', '/', views.index)
    app.router.add_route('POST', '/move/{dir}', views.move)
    app.router.add_route('POST', '/start', views.start)
    static_dir = os.path.join(FILE_PATH, "static")
    app.router.add_static('/static', static_dir)
    return app

# XXX combine these two functions
# def app_factory(global_config, **settings):
    # loop = asyncio.get_event_loop()
    # app = make_app(loop, settings)
    # return app
