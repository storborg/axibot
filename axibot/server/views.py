import logging

import io

from aiohttp import web
import aiohttp_themes

from .. import svg, planning, config, moves

from . import handlers
from .state import State

log = logging.getLogger(__name__)


@aiohttp_themes.template('index.html')
async def index(request):
    return {'text': 'Hello World!'}


def process_upload(svgdoc):
    pen_up_delay, pen_down_delay = \
        moves.calculate_pen_delays(config.PEN_UP_POSITION,
                                   config.PEN_DOWN_POSITION)

    paths = svg.extract_paths_string(svgdoc)
    paths = svg.preprocess_paths(paths)
    segments = svg.plan_segments(paths, resolution=config.CURVE_RESOLUTION)
    transits = svg.add_pen_transits(segments)
    step_transits = planning.convert_inches_to_steps(transits)
    segments_limits = planning.plan_velocity(step_transits)
    actions = planning.plan_actions(segments_limits,
                                    pen_up_delay=pen_up_delay,
                                    pen_down_delay=pen_down_delay)
    return actions


async def upload(request):
    app = request.app
    assert app['state'] in (State.idle_doc, State.idle_empty)

    data = await request.post()
    upload = data['file']
    log.info("Received uploaded file: %s", upload.filename)

    app['state'] = State.processing
    # Notify all clients we are now processing
    handlers.update_all_client_state(app)

    try:
        app['document'] = upload.file.read()
        app['actions'] = process_upload(app['document'])

    except Exception as e:
        app['state'] = State.idle_empty
        handlers.update_all_client_state(app)
        return web.Response(text='failure: %s' % e, status=500)

    app['state'] = State.idle_doc
    # Notify all clients we are now idle and ready to plot
    handlers.update_all_client_state(app)

    return web.Response(text='ok')


async def document(request):
    app = request.app
    if app['document']:
        return web.Response(text=app['document'],
                            content_type='image/svg+xml')
    else:
        return web.Response(status=404)
