from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pprint import pprint
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

    This also 'collapses points': that is, if there are two or more adjacent
    points in a segment are at the same position, they are combined into one.
    """
    spi = config.DPI_16X
    out = []
    for segment, pen_up in transits:
        points = []
        last_point = None
        for inches_point in segment:
            assert len(inches_point) == 2
            steps_point = (round(spi * inches_point[0]),
                           round(spi * inches_point[1]))
            if (last_point is None) or (steps_point != last_point):
                points.append(steps_point)
            last_point = steps_point
        out.append((points, pen_up))
    return out


def cornering_angle(a, b, c):
    """
    Given three points, compute the angle in radians between AB and BC.
    """
    assert a != b
    assert b != c

    ax, ay = a
    bx, by = b
    cx, cy = c
    x = (bx - ax)**2 + (by - ay)**2
    y = (bx - cx)**2 + (by - cy)**2
    z = (cx - ax)**2 + (cy - ay)**2

    arg = (x + y - z) / math.sqrt(4 * x * y)

    # Floating point error can accumulate here and give us an argument to
    # acos() that will be like 1.00000000000whatever
    # Catch that and just make it 1 or -1.

    if arg > 1:
        assert arg < 1.000002
        arg = 1
    elif arg < -1:
        assert arg > -1.000002
        arg = -1

    return math.acos(arg)


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


def dtarray_to_moves(start, end, dt_array):
    """
    Given a start point, an end point, and an array of linear distances/times,
    return the actions to move between the two points, with one move per point
    in the array.
    """
    assert end != start
    print("dtarray_to_moves %r -> %r" % (start, end))

    dist = distance(end, start)
    # assert end_dist == dist, "expected %r == %r" % (dt_array[-1][0], dist)
    xratio = (end[0] - start[0]) / dist
    yratio = (end[1] - start[1]) / dist

    dots = []
    for d, duration in dt_array:
        x = round(xratio * d)
        y = round(yratio * d)
        dots.append((x, y, duration))

    actions = []
    prev_x, prev_y = 0, 0
    for x, y, duration in dots:
        dx = x - prev_x
        dy = y - prev_y
        prev_x = x
        prev_y = y

        # Convert to AxiDraw coordinate space.
        m1 = dx + dy
        m2 = dx - dy

        duration = round(duration * 1000)
        actions.append(moves.XYMove(m1=m1, m2=m2, duration=duration))

        print("  pos %d, %d" % (x, y))

    return actions


def interpolate_distance_trapezoidal(vstart, accel_time, accel_dist,
                                     vend, decel_time, decel_dist,
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
            x += v * accel_timeslice
            v += vstep
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
            x += v * decel_timeslice
            v += vstep
            dtarray.append((x, decel_timeslice))

    return dtarray


def interpolate_distance_linear(dist, vstart, vend, accel_rate, timeslice):
    # Linear
    lin_accel = ((vend**2 - vstart**2) / (2 * dist))
    print("lin_accel %r" % lin_accel)
    lin_accel = min(lin_accel, accel_rate)
    lin_accel = max(lin_accel, -accel_rate)
    print("cropped lin_accel %r" % lin_accel)
    lin_time = (vend - vstart) / lin_accel
    print("lin_time %r" %  lin_time)

    vavg = (vend - vstart) / 2
    print("vavg %r" % vavg)
    lin_time = vavg / dist
    print("vavg based lin_time %r" % lin_time)

    x = 0
    v = vstart
    dtarray = []

    slices = int(math.floor(lin_time / timeslice))
    if not slices:
        return [(dist, dist / vavg)]
    print("slices %r" % slices)
    if slices:
        lin_timeslice = lin_time / slices
        print("lin_timeslice %r" % lin_timeslice)
        vstep = (vend - vstart) / slices
        print("vstep %r" % vstep)
        for n in range(slices):
            x += v * lin_timeslice
            v += vstep
            dtarray.append((x, lin_timeslice))
    else:
        # XXX ???
        dtarray.append((dist, timeslice))
    return dtarray


def interpolate_distance_triangular(vstart, vend, dist, accel_rate):
    timeslice = config.TIME_SLICE
    accel_time = ((math.sqrt((2 * vstart**2) +
                             (2 * vend**2) +
                             (4 * accel_rate * dist)) -
                   (2 * vstart)) /
                  (2 * accel_rate))
    accel_slices = int(math.floor(accel_time / timeslice))
    if accel_slices == 0:
        accel_time = 0

    vmax = vstart + (accel_time * accel_rate)

    decel_time = accel_time - (vend - vstart) / accel_rate
    decel_slices = int(math.floor(decel_time / timeslice))

    dtarray = []
    x = 0
    v = vstart

    if (accel_slices + decel_slices) > 4:
        # Triangular
        print("triangular")
        if accel_slices:
            accel_timeslice = accel_time / accel_slices
            vstep = (vmax - vstart) / (accel_slices + 1.0)
            for n in range(accel_slices):
                x += v * accel_timeslice
                v += vstep
                dtarray.append((x, accel_timeslice))

        if decel_slices:
            decel_timeslice = decel_time / decel_slices
            vstep = (vend - vmax) / (decel_slices + 1.0)
            for n in range(decel_slices):
                x += v * decel_timeslice
                v += vstep
                dtarray.append((x, decel_timeslice))
    elif vend == vstart:
        print("constant")
        if vstart:
            # Constant velocity that is non-zero
            return [(dist, dist / vstart)]
        else:
            # Segment that has to start and end at zero velocity, but is really
            # short. This is a really obnoxious case, for now we're just going
            # to set it to do the move in 100ms. Need to figure out the 'vmin'
            # which can be accelerated to instantaneously.
            return [(dist, 0.1)]
    else:
        print("linear")
        dtarray = interpolate_distance_linear(dist, vstart, vend, accel_rate,
                                              timeslice)

    pprint(dtarray)
    # assert end_dist == dist, "%r must == %r" % (dtarray[-1][0], dist)
    return dtarray


def interpolate_distance(dist, vstart, vend, vmax, accel_max, timeslice):
    """
    Given a distance to traverse, start and end velocities in the direction of
    movement, a maximum velocity, an acceleration rate, and a minimum
    timeslice, generated an array of (distance, time) points.

    Distancec units are motor steps.
    Velocity units are motor steps per second.
    Acceleration units are steps/second^2.
    Timeslice provided is in seconds.
    """
    print("vstart %r" % vstart)
    print("vend %r" % vend)
    print("vmax %r" % vmax)
    print("accel_max %r" % accel_max)

    accel_time = (vmax - vstart) / accel_max
    decel_time = (vmax - vend) / accel_max
    accel_dist = (vstart * accel_time) + (0.5 * accel_max * (accel_time**2))
    decel_dist = (vend * decel_time) + (0.5 * accel_max * (decel_time**2))

    print("accel_time %r" % accel_time)
    print("decel_time %r" % decel_time)
    print("accel_dist %r" % accel_dist)
    print("decel_dist %r" % decel_dist)

    if dist > (accel_dist + decel_dist + timeslice * vmax):
        print("trapezoidal")
        # Trapezoidal
        return interpolate_distance_trapezoidal(
            vstart, accel_time, accel_dist,
            vend, decel_time, decel_dist,
            vmax, dist)
    else:
        print("triangular or linear")
        # Triangular or linear
        return interpolate_distance_triangular(vstart, vend, dist, accel_max)


def interpolate_pair(start, vstart, end, vend, pen_up):
    """
    Given start/end positions, velocities, and pen state, return the array of
    distance/time to move between two points.

    Note that a given distance entry is the distance travelled *after* the
    point/move has been made.

    We want to always be accelerating at a constant rate, decelerating at a
    constant rate, or moving at the maximum velocity for this pen state.
    """
    print("interpolate_pair: %r, %r, %r, %r, %r" % (start, vstart,
                                                    end, vend,
                                                    pen_up))
    if pen_up:
        vmax = config.SPEED_PEN_UP
        accel_max = vmax / config.ACCEL_TIME_PEN_UP
    else:
        vmax = config.SPEED_PEN_DOWN
        accel_max = vmax / config.ACCEL_TIME_PEN_DOWN

    timeslice = config.TIME_SLICE

    dist = distance(end, start)

    assert vstart <= vmax, "%f must be <= %f" % (vstart, vmax)
    assert vend <= vmax, "%f must be <= %f" % (vend, vmax)
    return interpolate_distance(dist, vstart, vend, vmax, accel_max, timeslice)


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
            actions.extend(dtarray_to_moves(last_point, point, dist_array))
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
            last_pen_up = pen_up
        actions.extend(interpolate_segment(segment, pen_up))
    return actions
