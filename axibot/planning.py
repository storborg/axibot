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


def plan_actions(segments_limits, pen_up_delay, pen_down_delay):
    """
    Given a list of (start, end, vmax_start, vmax_end, pen_up) tuples as
    returned by plan_speed_limits(), return a list of moves, with acceleration
    and deceleration plotted between points.  Also add any pen state changes.

    Planning acceleration is non-trivial here, since it's possible to end up in
    a short segment where the initial speed is too high to decelerate to the
    speed limit at the end of the segment.
    """
    actions = []
    return actions
