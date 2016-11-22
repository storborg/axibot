import logging

import math

from .. import svg, planning, config
from ..action import PenUpMove, PenDownMove, XYMove

from . import handlers
from .state import State

log = logging.getLogger(__name__)


def step_segments_to_actions(app, step_segments):
    pen_up_delay = app['pen_up_delay']
    pen_down_delay = app['pen_down_delay']
    segments_limits = planning.plan_speed(step_segments)
    return planning.plan_actions(segments_limits,
                                 pen_up_delay=pen_up_delay,
                                 pen_down_delay=pen_down_delay)


def plan_pen_up_move(app, start, end):
    step_segments = [((start, end), True)]
    actions = step_segments_to_actions(app, step_segments)
    return actions


def plan_deceleration(app, position, v):
    """
    Given an initial position in steps, and an initial velocity vector in steps
    per millisecond, create a series of actions which will decelerate as
    quickly as possible, moving in the same direction.
    """
    # get config
    if app['pen_up']:
        vmax = config.SPEED_PEN_UP
        accel_time = config.ACCEL_TIME_PEN_UP
    else:
        vmax = config.SPEED_PEN_DOWN
        accel_time = config.ACCEL_TIME_PEN_DOWN

    # calculate distance required for deceleration
    vx, vy = v
    vmag = math.sqrt((vx**2) + (vy**2))
    x_accel_time = (abs(vx) / vmax) * accel_time
    x_accel_dist = x_accel_time * (vx / 2)
    y_accel_time = (abs(vy) / vmax) * accel_time
    y_accel_dist = y_accel_time * (vy / 2)

    # make a line extending from this position along that distance
    end = (int(round(position[0] + x_accel_dist)),
           int(round(position[1] + y_accel_dist)))

    # assert that it doesn't exceed the bounds of the machine
    # XXX

    # plan actions for this segment
    log.error("plan_deceleration: %s @ %s -> %s @ %s", position, vmag, end, 0)
    dtarray = planning.interpolate_pair(position, vmag,
                                        end, 0, app['pen_up'])
    return planning.dtarray_to_moves(position, end, dtarray)


def process_upload(app, svgdoc):
    paths = svg.extract_paths_string(svgdoc)
    paths = svg.preprocess_paths(paths)
    segments = svg.plan_segments(paths, resolution=config.CURVE_RESOLUTION)
    segments = svg.add_pen_up_moves(segments)
    step_segments = planning.convert_inches_to_steps(segments)
    return step_segments_to_actions(app, step_segments)


def process_pen_state(app, action):
    if isinstance(action, XYMove):
        dx = (action.m1 + action.m2) / 2
        dy = (action.m1 - action.m2) / 2
        lastx, lasty = app['position']
        app['position'] = lastx + dx, lasty + dy
    elif isinstance(action, PenUpMove):
        app['pen_up'] = True
    elif isinstance(action, PenDownMove):
        app['pen_up'] = False


async def cancel_to_origin(app, action):
    log.error("cancel_to_origin: start")
    if isinstance(action, PenUpMove):
        v = 0, 0
    elif isinstance(action, PenDownMove):
        v = 0, 0
    elif isinstance(action, XYMove):
        dx = (action.m1 + action.m2) / 2
        dy = (action.m1 - action.m2) / 2
        v = dx / action.duration, dy / action.duration
    else:
        raise ValueError("don't understand action: %r" % action)

    log.error("cancel_to_origin: generating deceleration trajectory")
    actions = []
    # plan trajectory from this v to zero
    # XXX enable this! and then make the pen up move go from the end of
    # deceleration
    # actions.extend(plan_deceleration(app, app['position'], v))
    # pen up if not already up
    if not app['pen_up']:
        actions.append(PenUpMove(app['pen_up_delay']))
    # plan move back to origin
    log.error("cancel_to_origin: generating move back to origin")
    actions.extend(plan_pen_up_move(app, app['position'], (0, 0)))
    bot = app['bot']

    log.error("cancel_to_origin: running actions")
    for action in actions:
        def run_action():
            bot.do(action)
        process_pen_state(app, action)
        await app.loop.run_in_executor(None, run_action)
        handlers.notify_state(app)

    log.error("cancel_to_origin: done")


async def plot_task(app):
    log.warn("plot_task: begin")
    app['state'] = State.plotting
    bot = app['bot']

    if app['pen_up'] is not True:
        bot.pen_up(app['pen_up_delay'])
        app['pen_up'] = True

    while True:
        actions = app['actions']
        action_index = app['action_index']
        action = actions[action_index]

        def run_action():
            bot.do(action)

        process_pen_state(app, action)
        await app.loop.run_in_executor(None, run_action)
        action_index += 1
        if action_index == len(actions):
            # Finished
            log.warn("plot_task: plotting complete")
            handlers.notify_job_complete(app)
            break

        app['action_index'] = action_index

        if app['state'] == State.canceling:
            log.warn("plot_task: canceling")
            # Decelerate, pen up, fastest move back to origin
            await cancel_to_origin(app, action)
            break
        # notify clients of state change
        handlers.notify_state(app)

    app['state'] = State.idle
    app['action_index'] = 0

    # send job complete message
    # notify clients of state change
    handlers.notify_state(app)
    log.warn("plot_task: end")


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


def resume(app):
    app['plot_task'] = app.loop.create_task(plot_task(app))


def pause(app):
    raise NotImplementedError


def cancel(app):
    app['state'] = State.canceling
    handlers.notify_state(app)
