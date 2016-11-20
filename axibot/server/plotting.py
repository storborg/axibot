import logging

from .. import moves, svg, planning, config

from . import handlers
from .state import State

log = logging.getLogger(__name__)


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


async def plot_task(app):
    app['state'] = State.plotting

    # XXX need to handle the servo setup, etc here.

    while True:
        actions = app['actions']
        action_index = app['action_index']
        action = actions[action_index]
        bot = app['bot']

        # XXX need to keep track of the robot position here to support
        # returning to origin

        def run_action():
            bot.do(action)

        await app.loop.run_in_executor(None, run_action)
        action_index += 1
        if action_index == len(actions):
            break
        app['action_index'] = action_index
        # notify clients of state change
        handlers.update_all_client_state(app)

    # XXX pen up and return to origin

    app['state'] = State.idle
    app['action_index'] = 0

    # send job complete message
    # notify clients of state change
    handlers.update_all_client_state(app)


async def manual_task(app, action):
    orig_state = app['state']
    log.error("manual task: set state to plotting")
    app['state'] = State.plotting
    handlers.update_all_client_state(app)
    bot = app['bot']

    def run():
        bot.do(action)

    await app.loop.run_in_executor(None, run)
    app['state'] = orig_state
    log.error("manual task: returned state to %s", orig_state)
    handlers.update_all_client_state(app)


def manual_pen_up(app):
    # XXX get the correct pen delay here
    app.loop.create_task(manual_task(app, moves.PenUpMove(1000)))


def manual_pen_down(app):
    # XXX get the correct pen delay here
    app.loop.create_task(manual_task(app, moves.PenDownMove(1000)))


def pause(app):
    app['state'] = State.paused
    app['plot_task'].cancel()

    # XXX pen up and return to origin


def resume(app):
    app['plot_task'] = app.loop.create_task(plot_task(app))


def cancel(app):
    app['state'] = State.idle
    app['action_index'] = 0
    app['plot_task'].cancel()

    # XXX pen up and return to origin
