import logging

from .. import svg, planning, config
from ..action import PenUpMove, PenDownMove

from . import handlers
from .state import State

log = logging.getLogger(__name__)


def process_upload(app, svgdoc):
    pen_up_delay = app['pen_up_delay']
    pen_down_delay = app['pen_down_delay']

    paths = svg.extract_paths_string(svgdoc)
    paths = svg.preprocess_paths(paths)

    segments = svg.plan_segments(paths, resolution=config.CURVE_RESOLUTION)
    segments = svg.add_pen_up_moves(segments)
    step_segments = planning.convert_inches_to_steps(segments)
    segments_limits = planning.plan_speed(step_segments)
    actions = planning.plan_actions(segments_limits,
                                    pen_up_delay=pen_up_delay,
                                    pen_down_delay=pen_down_delay)
    return actions


async def plot_task(app):
    log.warn("plot_task: begin")
    app['state'] = State.plotting

    # XXX need to handle the servo setup, etc here.

    while True:
        actions = app['actions']
        action_index = app['action_index']
        action = actions[action_index]
        log.warn("plot_task: action %s", action)
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
        handlers.notify_state(app)

    # XXX pen up and return to origin

    app['state'] = State.idle
    app['action_index'] = 0

    # send job complete message
    # notify clients of state change
    handlers.notify_state(app)
    log.warn("plot_task: end")


async def pause_task(app):
    pass


async def cancel_task(app):
    pass


async def manual_task(app, action):
    orig_state = app['state']
    log.error("manual task: set state to plotting")
    app['state'] = State.plotting
    handlers.notify_state(app)
    bot = app['bot']

    def run():
        bot.do(action)

    await app.loop.run_in_executor(None, run)
    app['state'] = orig_state
    log.error("manual task: returned state to %s", orig_state)
    handlers.notify_state(app)


def manual_pen_up(app):
    pen_up_delay = app['pen_up_delay']
    app.loop.create_task(manual_task(app, PenUpMove(pen_up_delay)))


def manual_pen_down(app):
    pen_down_delay = app['pen_down_delay']
    app.loop.create_task(manual_task(app, PenDownMove(pen_down_delay)))


def pause(app):
    app['state'] = State.paused
    app['plot_task'].cancel()
    app.loop.create_task(pause_task(app))


def resume(app):
    app['plot_task'] = app.loop.create_task(plot_task(app))


def cancel(app):
    app['state'] = State.idle
    app['action_index'] = 0
    app['plot_task'].cancel()
    app.loop.create_task(cancel_task(app))
