from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import math

from . import config, moves


def distance(a, b):
    """
    Distance between two points.
    """
    return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)


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
    that corner. Ensure that the segment starts and ends at zero velocity.
    """
    out = []
    out.append((segment[0], 0.0))

    for a, b, c in zip(segment[:-2], segment[1:-1], segment[2:]):
        angle = cornering_angle(a, b, c)
        limit = cornering_velocity(angle, pen_up)
        out.append((b, limit))

    out.append((segment[-1], 0.0))
    return out


def segment_acceleration_limits(segment, pen_up):
    """
    Given a segment w/ speed limits and pen state, tag each point with the
    target speed for that corner. This will possibly reduce speeds from the
    speed limit, to account for acceleration and deceleration requirements.

    We'll do two passes through the list of points: one forward for
    acceleration, one backward for deceleration.
    """
    if pen_up:
        vmax = config.SPEED_PEN_UP
        accel_time = config.ACCEL_TIME_PEN_UP
    else:
        vmax = config.SPEED_PEN_DOWN
        accel_time = config.ACCEL_TIME_PEN_DOWN
    accel_rate = vmax / accel_time

    out = []
    last_point, last_speed = segment[0]
    for point, speed_limit in segment[1:]:
        dist = distance(point, last_point)
        # can we accelerate from last_speed to speed_limit in this distance?
        top_speed = math.sqrt((2 * accel_rate * dist) + last_speed**2)
        # if not we need to limit the speed at this point
        speed = max(speed_limit, top_speed)
        out.append((point, speed))
        last_point = point
        last_speed = speed

    return out


def plan_velocity(transits):
    """
    Given a list of (segment, pen_up) tuples, tag each segment with a target
    velocity for that corner. This combines two limits:

    - The max speed at which we can plot through a given corner, based on how
    tight that corner is and the pen state.
    - The acceleration/deceleration limit.

    Both of these limits serve to avoid the pen carriage oscillating and thus
    making the pen line squiggly, or just slamming the motors around and
    causing wear on the machine.
    """
    out = []
    for segment, pen_up in transits:
        points = segment_corner_limits(segment, pen_up)
        # Calculate forward acceleration
        points = segment_acceleration_limits(points, pen_up)
        # Calculate reverse acceleration (deceleration)
        points = segment_acceleration_limits(points[::-1], pen_up)
        points = points[::-1]
        out.append((points, pen_up))
    return out


def distance_array_to_moves(start, end, dist_array):
    """
    Given a start point, an end point, and an array of linear distances, return
    the actions to move between the two points, with one move per linear
    distance.
    """


def interpolate_pair(start, vstart, end, vend, pen_up):
    """
    Given start/end positions, velocities, and pen state, return the array of
    distance per timeslice to move between two points.

    We basically want to always be accelerating at a constant rate,
    decelerating at a constant rate, or moving at the maximum velocity for this
    pen state.
    """
    pass


def interpolate_segment(segment, pen_up):
    """
    Given a segment with assigned speeds at each point, and a max
    acceleration/deceleration rate, create the moves to traverse the segment.
    """
    assert segment[0][1] == 0
    assert segment[-1][1] == 0

    actions = []
    # Iterate over point pairs.
    last_point, last_speed = segment[0]
    for point, speed in segment[1:]:
        dist_array = interpolate_pair(last_point, last_speed,
                                      point, speed, pen_up)
        actions.extend(distance_array_to_moves(last_point, point, dist_array))
    return actions


def plan_actions(segments_with_velocity, pen_up_delay, pen_down_delay):
    """
    Given a list of (segment, pen_up) tuples as returned by plan_velocity(),
    return a list of moves. Also add any pen state changes.
    """
    actions = []
    last_pen_up = True
    for segment, pen_up in segments_with_velocity:
        if pen_up != last_pen_up:
            if pen_up:
                actions.append(moves.PenUpMove(pen_up_delay))
            else:
                actions.append(moves.PenDownMove(pen_down_delay))
        actions.extend(interpolate_segment(segment, pen_up))
    return actions
