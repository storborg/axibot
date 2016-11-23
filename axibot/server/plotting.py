import logging

import math

from .. import svg, planning, config
from ..action import PenUpMove, PenDownMove, XYMove

from . import handlers
from .state import State

log = logging.getLogger(__name__)


def estimate_time(actions):
    return sum(action.time() for action in actions) / 1000.


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

    Return a tuple of (end point, actions)
    """
    if app['pen_up']:
        vmax = config.SPEED_PEN_UP
        accel_time = config.ACCEL_TIME_PEN_UP
    else:
        vmax = config.SPEED_PEN_DOWN
        accel_time = config.ACCEL_TIME_PEN_DOWN

    # Calculate distance required for deceleration.
    vx, vy = v
    vmag = math.sqrt((vx**2) + (vy**2))
    x_accel_time = (abs(vx) / vmax) * accel_time
    x_accel_dist = x_accel_time * (vx / 2)
    y_accel_time = (abs(vy) / vmax) * accel_time
    y_accel_dist = y_accel_time * (vy / 2)

    # Ugh
    if vmag > vmax:
        vmag = vmax

    if not (x_accel_dist or y_accel_dist):
        # Don't need to decelerate.
        return position, []

    # Make a line extending from this position along that distance.
    end = (int(round(position[0] + x_accel_dist)),
           int(round(position[1] + y_accel_dist)))

    # Assert that it doesn't exceed the bounds of the machine.
    # XXX

    # Plan the actions for this deceleration segment.
    dtarray = planning.interpolate_pair(position, vmag,
                                        end, 0, app['pen_up'])
    return end, planning.dtarray_to_moves(position, end, dtarray)


def process_upload(app, svgdoc):
    paths = svg.extract_paths_string(svgdoc)
    paths = svg.preprocess_paths(paths)
    segments = svg.plan_segments(paths, resolution=config.CURVE_RESOLUTION)
    segments = svg.add_pen_up_moves(segments)
    step_segments = planning.convert_inches_to_steps(segments)
    return step_segments_to_actions(app, step_segments)


def update_bot_state(app, action):
    if isinstance(action, XYMove):
        dx = (action.m1 + action.m2) / 2
        dy = (action.m1 - action.m2) / 2
        lastx, lasty = app['position']
        app['position'] = lastx + dx, lasty + dy
        app['consumed_time'] += (action.duration / 1000.)
    elif isinstance(action, PenUpMove):
        app['pen_up'] = True
        app['consumed_time'] += (action.delay / 1000.)
    elif isinstance(action, PenDownMove):
        app['pen_up'] = False
        app['consumed_time'] += (action.delay / 1000.)


async def cancel_to_origin(app, action):
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

    # plan trajectory from this v to zero
    decel_end, actions = plan_deceleration(app, app['position'], v)

    # lift pen up if not already up
    if not app['pen_up']:
        actions.append(PenUpMove(app['pen_up_delay']))

    # plan move back to origin
    actions.extend(plan_pen_up_move(app, decel_end, (0, 0)))
    orig_estimated = app['estimated_time']
    app['estimated_time'] = estimate_time(actions)
    app['consumed_time'] = 0
    bot = app['bot']

    for action in actions:
        def run_action():
            bot.do(action)
        update_bot_state(app, action)
        await app.loop.run_in_executor(None, run_action)
        handlers.notify_state(app)

    app['estimated_time'] = orig_estimated
    app['consumed_time'] = 0


async def plot_task(app):
    log.debug("plot_task: begin")
    app['state'] = State.plotting
    bot = app['bot']
    app['consumed_time'] = 0

    if app['pen_up'] is not True:
        bot.pen_up(app['pen_up_delay'])
        app['pen_up'] = True

    while True:
        actions = app['actions']
        action_index = app['action_index']
        action = actions[action_index]

        def run_action():
            bot.do(action)

        update_bot_state(app, action)
        await app.loop.run_in_executor(None, run_action)
        action_index += 1
        if action_index == len(actions):
            # Finished
            log.debug("plot_task: plotting complete")
            handlers.notify_job_complete(app)
            break

        app['action_index'] = action_index

        if app['state'] == State.canceling:
            log.debug("plot_task: canceling")
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
    log.debug("manual task: set state to plotting")
    app['state'] = State.plotting
    handlers.notify_state(app)
    bot = app['bot']

    def run():
        bot.do(action)

    await app.loop.run_in_executor(None, run)
    app['state'] = orig_state
    log.debug("manual task: returned state to %s", orig_state)
    handlers.notify_state(app)


def manual_pen_up(app):
    pen_up_delay = app['pen_up_delay']
    app.loop.create_task(manual_task(app, PenUpMove(pen_up_delay)))


def manual_pen_down(app):
    pen_down_delay = app['pen_down_delay']
    app.loop.create_task(manual_task(app, PenDownMove(pen_down_delay)))


def resume(app):
    app.loop.create_task(plot_task(app))


def cancel(app):
    app['state'] = State.canceling
    handlers.notify_state(app)
