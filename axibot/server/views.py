import logging

import aiohttp_themes

log = logging.getLogger(__name__)


@aiohttp_themes.template('index.html')
async def index(request):
    return {'document': request.app['document']}
