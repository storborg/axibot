import aiohttp_themes


@aiohttp_themes.template('index.html')
async def index(request):
    return {'text': 'Hello World!'}


# XXX: Figure out how to handle these
async def move(request):
    move_direction = request.match_info['dir']
    return "moved %s" % move_direction


async def start(request):
    return ""
