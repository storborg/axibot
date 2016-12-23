import logging

import aiohttp_mako

log = logging.getLogger(__name__)


@aiohttp_mako.template('index.html')
async def index(request):
    return {'document': request.app['job'].document}
