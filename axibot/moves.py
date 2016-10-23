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
