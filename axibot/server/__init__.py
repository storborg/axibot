import logging
import os
import os.path

from aiohttp import web
import aiohttp_mako

from . import views

log = logging.getLogger(__name__)


FILE_PATH = os.path.dirname(os.path.realpath(__file__))


def make_app():
    app = web.Application()

    aiohttp_mako.setup(
        app, input_encoding='utf-8',
        output_encoding='utf-8',
        default_filters=['decode.utf8'],
        directories=[os.path.join(FILE_PATH, "templates")])

    app.router.add_route('GET', '/', views.index)
    app.router.add_route('POST', '/move/{dir}', views.move)
    app.router.add_route('POST', '/start', views.start)
    static_dir = os.path.join(FILE_PATH, "static")
    app.router.add_static('/static', static_dir)
    return app


def serve(opts):
    app = make_app()
    web.run_app(app, port=opts.port)
