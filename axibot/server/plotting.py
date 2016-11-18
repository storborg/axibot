from .. import moves, svg, planning, config

from . import handlers
from .state import State


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


def set_document(app, f):
    app['state'] = State.processing
    # Notify all clients we are now processing
    handlers.update_all_client_state(app)

    try:
        app['document'] = svgdoc = f.read()
        app['actions'] = process_upload(svgdoc)

    except Exception as e:
        app['state'] = State.idle_empty
        handlers.update_all_client_state(app)
        raise

    app['state'] = State.idle_doc
    # Notify all clients we are now idle and ready to plot
    handlers.update_all_client_state(app)
