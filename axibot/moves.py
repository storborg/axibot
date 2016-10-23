import math

from pprint import pformat

from . import config


class Move:
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, pformat(self.__dict__))

    def __str__(self):
        attrs = ['%s:%s' % (k, v) for k, v in self.__dict__.items()]
        return '%s %s' % (self.name, attrs.join(' '))


class PenUpMove(Move):
    name = 'pen_up'

    def __init__(self, delay):
        self.delay = delay


class PenDownMove(Move):
    name = 'pen_down'

    def __init__(self, delay):
        self.delay = delay


class XYMove(Move):
    name = 'xy_move'

    def __init__(self, dx, dy, duration):
        self.dx = dx
        self.dy = dy
        self.duration = duration


class XYAccelMove(Move):
    name = 'xy_accel_move'

    def __init__(self, dx, dy, v_initial, v_final):
        self.dx = dx
        self.dy = dy
        self.v_initial = v_initial
        self.v_final = v_final


class ABMove(Move):
    name = 'ab_move'

    def __init__(self, da, db, duration):
        self.da = da
        self.db = db
        self.duration = duration


# Precise V5 pens. Totally guessing here on values.
pen_colors = {
    'black': (0, 0, 0),
    'blue': (0, 0, 255),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'purple': (127, 255, 0),
    'lightblue': (80, 80, 255),
    'pink': (255, 127, 127),
}


def calculate_pen_delays(up_position, down_position):
    """
    The AxiDraw motion controller must know how long to wait after giving a
    'pen up' or 'pen down' command. This requires calculating the speed that
    the servo can move to or from the two respective states. This function
    performs that calculation and returns a tuple of (pen_up_delay,
    pen_down_delay). All delays are in milliseconds.
    """
    assert up_position > down_position

    # Math initially taken from axidraw inkscape driver, but I think this can
    # be sped up a bit. We might also want to use different speeds for up/down,
    # due to the added weight of the pen slowing down the servo in the 'up'
    # direction.
    dist = up_position - down_position
    time = int((1000. * dist) / config.SERVO_SPEED)

    return ((time + config.EXTRA_PEN_UP_DELAY),
            (time + config.EXTRA_PEN_DOWN_DELAY))


def plot_segment_with_velocity(p0, p1, v_initial, v_final, pen_up):
    """
    Generate the low-level machine moves to plot a straight line segment, with
    a trapezoidal velocity profile. That is, ramp velocity up to v_final,
    starting from v_initial, move at a constant v_final, then ramp velocity
    back down to v_initial.

    Move from p0 (x, y) to p1 (x, y).

    Units are inches (for position points) or inches per second (for velocity).
    """
    x0, y0 = p0
    x1, y1 = p1

    # Steps per inch of microstepping.
    spi = config.DPI_16X

    # XXX should this check bounds limits??

    # convert to motor step units
    xmove_ideal = spi * (x1 - x0)
    ymove_ideal = spi * (y1 - y0)
    v_initial *= spi
    v_final *= spi

    motor_steps1 = int(round(xmove_ideal + ymove_ideal))
    motor_steps2 = int(round(xmove_ideal - ymove_ideal))

    plot_distance = math.sqrt((motor_steps1**2) + (motor_steps2**2))
    if plot_distance < 1.0:
        return []

    # Get limits based on pen up/down state.
    if (not pen_up) or (plot_distance < (spi * config.SHORT_THRESHOLD)):
        speed = config.SPEED_PEN_DOWN
        accel_rate = speed / config.ACCEL_TIME_PEN_DOWN
    else:
        speed = config.SPEED_PEN_UP
        accel_rate = speed / config.ACCEL_TIME_PEN_UP

    # Obey the speed limit plz
    v_initial = min(v_initial, speed)
    v_final = min(v_final, speed)

    # Times to reach maximum speed, from our initial velocity
    # vMax = vi + a*t  =>  t = (vMax - vi)/a
    # vf = vMax - a*t   =>  t = -(vf - vMax)/a = (vMax - vf)/a
    # -- These are _maximum_ values. We often do not have enough time/space to
    # reach full speed.
    t_accel = (speed - v_initial) / accel_rate
    t_decel = (speed - v_final) / accel_rate

    # Distance required to reach full speed, from start at speed v_initial
    accel_dist = (v_initial * t_accel) + (0.5 * accel_rate * (t_accel**2))
    decel_dist = (v_final * t_decel) + (0.5 * accel_rate * (t_decel**2))

    # Slice travel into slices of time that are at least 50ms long
    timeslice = config.TIME_SLICE

    time_elapsed = 0.0
    position = 0.0
    velocity = v_initial

    duration_array = []
    distance_array = []

    if plot_distance > (accel_dist + decel_dist + timeslice * speed):
        # Make a trapezoid velocity profile

        print("accel phase, t_accel:%s, timeslice:%s" % (t_accel, timeslice))
        intervals = int(math.floor(t_accel / timeslice))
        if intervals:
            interval_time = t_accel / intervals
            velocity_step = (speed - v_initial) / (intervals + 1.0)
            for ii in range(intervals):
                print("  step")
                velocity += velocity_step
                time_elapsed += interval_time
                position += velocity * interval_time
                duration_array.append(int(round(time_elapsed * 1000.0)))
                # distance along the line of travel
                distance_array.append(position)

        print("coast phase")
        coast_distance = plot_distance - (accel_dist + decel_dist)
        if coast_distance > (timeslice * speed):
            velocity = speed
            cruising_time = coast_distance / velocity
            time_elapsed += cruising_time
            duration_array.append(int(round(time_elapsed * 1000.0)))
            position += velocity * cruising_time
            distance_array.append(position)

        print("decel phase, t_decel:%s, timeslice:%s" % (t_decel, timeslice))
        intervals = int(math.floor(t_decel / timeslice))
        if intervals:
            interval_time = t_decel / intervals
            velocity_step = (speed - v_final) / (intervals + 1.0)
            for ii in range(intervals):
                print("  step")
                velocity -= velocity_step
                time_elapsed += interval_time
                position += velocity * interval_time
                duration_array.append(int(round(time_elapsed * 1000.0)))
                # distance along the line of travel
                distance_array.append(position)

    else:
        # Make a triangle velocity profile
        raise NotImplementedError(
            "triangle velocity profile not supported yet")

    dest_array1 = []
    dest_array2 = []
    prev_motor1 = 0
    prev_motor2 = 0
    prev_time = 0

    # given time & distance motion arrays, compute actual moves
    for ii in range(len(distance_array)):
        frac_distance = distance_array[ii] / position
        dest_array1.append(int(round(frac_distance * motor_steps1)))
        dest_array2.append(int(round(frac_distance * motor_steps2)))

    prev_motor1 = 0
    prev_motor2 = 0
    prev_time = 0

    actions = []

    for ii in range(len(dest_array1)):
        move_steps1 = dest_array1[ii] - prev_motor1
        move_steps2 = dest_array2[ii] - prev_motor2
        move_time = duration_array[ii] - prev_time
        prev_time = duration_array[ii]

        # don't allow zero-time moves.
        if (move_time < 1):
            move_time = 1

        # don't allow too-slow movements of this axis
        if (abs((float(move_steps1) / float(move_time))) < 0.002):
            move_steps1 = 0
        if (abs((float(move_steps2) / float(move_time))) < 0.002):
            move_steps2 = 0

        prev_motor1 += move_steps1
        prev_motor2 += move_steps2

        # if at least one motor step is required for this move....
        if move_steps1 or move_steps2:
            actions.append(XYMove(move_steps1, move_steps2, move_time))

    return actions
