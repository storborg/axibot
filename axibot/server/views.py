import aiohttp_themes


@aiohttp_themes.template('index.html')
async def index(request):
    return {'text': 'Hello World!'}

async def start(request):
    return ""

async def toggle_pen(request):
    return ""
