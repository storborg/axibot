import math

from . import config


def cornering_angle(a, b, c):
    """
    Given three points, compute the angle in radians between AB and BC.
    """
    ax, ay = a
    bx, by = b
    cx, cy = c
    return abs(math.atan2(ay - by, ax - bx) - math.atan2(cy - by, cx - bx))


def cornering_velocity(angle, pen_up):
    """
    Given a corner angle in radians, compute the desired cornering velocity.

    An angle of pi can go full speed. An angle of zero needs to fully changeh
    direction, so it needs to have zero velocity. Everywhere in between...?

    XXX figure this out
    """
    ratio = angle / math.pi
    max_speed = config.SPEED_PEN_UP if pen_up else config.SPEED_PEN_DOWN
    return ratio * max_speed


def segment_corner_limits(segment, pen_up):
    """
    Given a segment and pen state, tag each point with the 'speed limit' for
    that corner.
    """
    out = []
    out.append((segment[0], 0.0))

    for a, b, c in zip(segment[:-2], segment[1:-1], segment[2:]):
        angle = cornering_angle(a, b, c)
        limit = cornering_velocity(angle, pen_up)
        out.append((b, limit))

    out.append((segment[-1], 0.0))
    return out


def plan_speed_limits(transits):
    """
    Given a list of (segment, pen_up) tuples, return a list of
    (start, end, vmax_start, vmax_end, pen_up) tuples.
    """
    out = []
    for segment, pen_up in transits:
        points = segment_corner_limits(segment, pen_up)
        prev_point, prev_speed_limit = points[0]
        for point, speed_limit in points[1:]:
            out.append((prev_point, point,
                        prev_speed_limit, speed_limit,
                        pen_up))
            prev_point = point
            prev_speed_limit = speed_limit

    return out


def plan_acceleration(start, end, v_start, vmax_end, pen_up):
    """
    Given start and end points, start and end speed limits, and the pen state
    for this line, compute the desired velocity profile along the line.

    Return the list of moves.

    Also return the actual final speed, so that it can be used as the initial
    speed for the start of the next segment.

    Velocity profile can either be:
        - trapezoidal (accelerate, constant, decelerate)
        - triangular (accelerate, decelerate)
        - linear (accelerate OR decelerate)

    Begin by computing the required acceleration time from vmax_start to the
    max speed and the deceleration time from max speed to vmax_end.
    """
    vmax_all = config.SPEED_PEN_UP if pen_up else config.SPEED_PEN_DOWN
    accel_rate = vmax_all / (config.ACCEL_TIME_PEN_UP
                             if pen_up else
                             config.ACCEL_TIME_PEN_DOWN)
    assert vmax_start <= vmax_all
    assert vmax_end <= vmax_all

    dist = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)

    accel_time = (vmax_all - vmax_start) / accel_rate
    decel_time = (vmax_all - vmax_end) / accel_rate
    accel_dist = (vmax_start * accel_time) + (0.5 * accel_rate * (t_accel**2))
    decel_dist = (vmax_end * decel_time) + (0.5 * accel_rate * (t_decel**2))

    timeslice = config.TIME_SLICE

    if dist > (accel_dist + decel_dist + (timeslice * vmax_all)):
        # Trapezoidal velocity profile.
        pass
    elif dist > accel_dist:
        # Triangular
        # We have enough time to accelerate to full speed, but not decelerate.
        # So instead we'll just go as fast as we can and still have enough
        # deceleration time.
        pass
    else:
        # Linear
        # We can't even reach the max speed anywhere in this segment. So
        # we'll just accelerate to vmax_end, if we can.
        pass

    return v, actions


def plan_moves(segments_limits):
    """
    Given a list of (start, end, vmax_start, vmax_end, pen_up) tuples, return a
    list of moves, with acceleration and deceleration plotted between points.
    Also add any pen state changes.
    """
    v_last = 0
    pen_up_last = False

    actions = []

    for start, end, vmax_start, vmax_end, pen_up in segments_limits:
        if pen_up != pen_up_last:
            # Add pen move
            if pen_up:
                # XXX get the right delay
                actions.append(moves.PenUpMove(1000))
            else:
                # XXX get the right delay
                actions.append(moves.PenDownMove(1000))
        assert v_last <= vmax_start
        v_last, seg_actions = plan_acceleration(start, end, v_last, vmax_end, pen_up)
        actions.extend(seg_actions)

    return actions
