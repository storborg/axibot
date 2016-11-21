import logging

from aiohttp import web
import aiohttp_themes

log = logging.getLogger(__name__)


@aiohttp_themes.template('index.html')
async def index(request):
    return {'text': 'Hello World!'}


async def document(request):
    app = request.app
    if app['document']:
        return web.Response(text=app['document'],
                            headers={'Cache-Control': 'no-store'},
                            content_type='image/svg+xml')
    else:
        return web.Response(status=404)
