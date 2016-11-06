from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import math

from . import config, moves


def distance(a, b):
    """
    Distance between two points.
    """
    return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)


def convert_inches_to_steps(transits):
    """
    Take the output from add_pen_transits() and convert all points from inches
    to steps.
    """
    spi = config.DPI_16X
    out = []
    for segment, pen_up in transits:
        points = []
        for point in segment:
            assert len(point) == 2
            points.append((spi * point[0], spi * point[1]))
        out.append((points, pen_up))
    return out


def cornering_angle(a, b, c):
    """
    Given three points, compute the angle in radians between AB and BC.
    """
    ax, ay = a
    bx, by = b
    cx, cy = c
    rad = abs(math.atan2(ay - by, ax - bx) - math.atan2(cy - by, cx - bx))
    assert rad < (2 * math.pi)
    assert rad >= 0
    if rad > math.pi:
        rad -= math.pi
    return rad


def cornering_velocity(angle, pen_up):
    """
    Given a corner angle in radians, compute the desired cornering velocity.

    An angle of pi can go full speed. An angle of zero needs to fully changeh
    direction, so it needs to have zero velocity. Everywhere in between...?

    XXX figure this out
    """
    ratio = angle / math.pi
    assert ratio <= 1.0
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
    assert segment
    if pen_up:
        vmax = config.SPEED_PEN_UP
        accel_time = config.ACCEL_TIME_PEN_UP
    else:
        vmax = config.SPEED_PEN_DOWN
        accel_time = config.ACCEL_TIME_PEN_DOWN
    accel_rate = vmax / accel_time

    out = []
    last_point, last_speed = segment[0]
    out.append((last_point, last_speed))
    for point, speed_limit in segment[1:]:
        dist = distance(point, last_point)
        # can we accelerate from last_speed to speed_limit in this distance?
        top_speed = math.sqrt((2 * accel_rate * dist) + last_speed**2)
        # if not we need to limit the speed at this point
        speed = min(speed_limit, top_speed)
        assert speed <= vmax
        out.append((point, speed))
        last_point = point
        last_speed = speed

    assert out
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
        assert segment
        points = segment_corner_limits(segment, pen_up)
        # Calculate forward acceleration
        points = segment_acceleration_limits(points, pen_up)
        assert points
        # Calculate reverse acceleration (deceleration)
        points = segment_acceleration_limits(points[::-1], pen_up)
        assert points
        points = points[::-1]
        assert points
        out.append((points, pen_up))
    return out


def distance_array_to_moves(start, end, dt_array):
    """
    Given a start point, an end point, and an array of linear distances/times,
    return the actions to move between the two points, with one move per point
    in the array.
    """
    assert end != start

    xdiff = end[0] - start[0]
    ydiff = end[1] - start[1]
    dist = distance(end, start)
    xratio = xdiff / dist
    yratio = ydiff / dist
    last_x, last_y = start
    last_t = 0

    actions = []
    for d, t in dt_array:
        duration = t - last_t
        new_x = xratio * d
        new_y = yratio * d

        dx = new_x - last_x
        dy = new_y - last_y

        # Convert to AxiDraw coordinate space.
        m1 = dx + dy
        m2 = dx - dy

        actions.append(moves.XYMove(m1=m1, m2=m2, duration=duration))

        last_x = new_x
        last_y = new_y
        last_t = t

    return actions


def interpolate_pair_trapezoidal(start, vstart, accel_time, accel_dist,
                                 end, vend, decel_time, decel_dist,
                                 vmax, dist):
    timeslice = config.TIME_SLICE
    accel_slices = int(math.floor(accel_time / timeslice))
    decel_slices = int(math.floor(decel_time / timeslice))

    dtarray = []

    x = 0
    v = vstart

    if accel_slices:
        accel_timeslice = accel_time / accel_slices
        vstep = (vmax - vstart) / (accel_slices + 1)
        for n in range(accel_slices):
            v += vstep
            x += v * accel_timeslice
            dtarray.append((x, accel_timeslice))

    coast_dist = dist - (accel_dist + decel_dist)
    if coast_dist > (timeslice * vmax):
        v = vmax
        x += coast_dist
        dtarray.append((x, coast_dist / v))

    if decel_slices:
        decel_timeslice = decel_time / decel_slices
        vstep = (vend - vmax) / (decel_slices + 1)
        for n in range(decel_slices):
            v += vstep
            x += v * decel_timeslice
            dtarray.append((x, decel_timeslice))

    return dtarray


def interpolate_pair_triangular(start, vstart,
                                end, vend,
                                vmax, dist, accel_rate):
    timeslice = config.TIME_SLICE
    accel_time = ((math.sqrt((2 * vstart**2) +
                             (2 * vend**2) +
                             (4 * accel_rate * dist)) -
                   (2 * vstart)) /
                  (2 * accel_rate))
    accel_slices = int(math.floor(accel_time / timeslice))
    if accel_slices == 0:
        accel_time = 0

    decel_time = accel_time - (vend - vstart) / accel_rate
    decel_slices = int(math.floor(decel_time / timeslice))

    dtarray = []
    x = 0
    v = vstart

    if (accel_slices + decel_slices) > 4:
        # Triangular
        if accel_slices:
            accel_timeslice = accel_time / accel_slices
            vstep = (vmax - vstart) / (accel_slices + 1.0)
            for n in range(accel_slices):
                v += vstep
                x += v * accel_timeslice
                dtarray.append((x, accel_timeslice))

        if decel_slices:
            decel_timeslice = decel_time / decel_slices
            vstep = (vend - vmax) / (decel_slices + 1.0)
            for n in range(decel_slices):
                v += vstep
                x += v * decel_timeslice
                dtarray.append((x, decel_timeslice))
    elif vend == vstart:
        if vstart:
            # Constant velocity that is non-zero
            return [(dist, dist / vstart)]
        else:
            # Segment that has to start and end at zero velocity, but is really
            # short. This is a really obnoxious case, for now we're just going
            # to set it to do the move in 100ms.
            # XXX ????
            return [(dist, 0.1)]
    else:
        # Linear
        lin_accel = ((vend**2 - vstart**2) / (2 * dist))
        lin_accel = min(lin_accel, accel_rate)
        lin_accel = max(lin_accel, -accel_rate)
        lin_time = (vend - vstart) / lin_accel

        slices = int(math.floor(lin_time / timeslice))
        if slices:
            lin_timeslice = lin_time / timeslice
            vstep = (vend - vstart) / (slices + 1.0)
            for n in range(slices):
                v += vstep
                x += v * lin_timeslice
                dtarray.append((x, lin_timeslice))
        else:
            # XXX ???
            dtarray.append((dist, timeslice))

    return dtarray


def interpolate_pair(start, vstart, end, vend, pen_up):
    """
    Given start/end positions, velocities, and pen state, return the array of
    distance/time to move between two points.

    We want to always be accelerating at a constant rate, decelerating at a
    constant rate, or moving at the maximum velocity for this pen state.
    """
    if pen_up:
        vmax = config.SPEED_PEN_UP
        accel_rate = vmax / config.ACCEL_TIME_PEN_UP
    else:
        vmax = config.SPEED_PEN_DOWN
        accel_rate = vmax / config.ACCEL_TIME_PEN_DOWN

    timeslice = config.TIME_SLICE

    dist = distance(end, start)

    assert vstart < vmax
    assert vend < vmax
    accel_time = (vmax - vstart) / accel_rate
    decel_time = (vmax - vend) / accel_rate
    accel_dist = (vstart * accel_time) + (0.5 * accel_rate * (accel_time**2))
    decel_dist = (vend * decel_time) + (0.5 * accel_rate * (decel_time**2))

    if dist > (accel_dist + decel_dist + timeslice * vmax):
        # Trapezoidal
        return interpolate_pair_trapezoidal(
            start, vstart, accel_time, accel_dist,
            end, vend, decel_time, decel_dist,
            vmax, dist)
    else:
        # Triangular or linear
        return interpolate_pair_triangular(
            start, vstart,
            end, vend,
            vmax, dist, accel_rate,
        )


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
        if point != last_point:
            dist_array = interpolate_pair(last_point, last_speed,
                                          point, speed, pen_up)
            actions.extend(distance_array_to_moves(last_point, point, dist_array))
        last_point = point
        last_speed = speed
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
