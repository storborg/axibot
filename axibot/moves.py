from pprint import pformat

from xml.etree import ElementTree


class Move:
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, pformat(self.__dict__))


class PenUpMove(Move):
    def __init__(self, delay):
        self.delay = delay

    def __str__(self):
        return "PENUP"


class PenDownMove(Move):
    def __init__(self, delay):
        self.delay = delay

    def __str__(self):
        return "PENDOWN"


class XYMove(Move):
    def __init__(self, dx, dy, duration):
        self.dx = dx
        self.dy = dy
        self.duration = duration

    def __str__(self):
        return "XY\t%s\t%s\t%s" % (self.dx, self.dy, self.duration)


class XYAccelMove(Move):
    def __init__(self, dx, dy, v_initial, v_final):
        self.dx = dx
        self.dy = dy
        self.v_initial = v_initial
        self.v_final = v_final

    def __str__(self):
        return "XYACCEL\t%s\t%s\t%s\t%s" % (self.dx, self.dy,
                                            self.v_initial, self.v_final)


class ABMove(Move):
    def __init__(self, da, db, duration):
        self.da = da
        self.db = db
        self.duration = duration

    def __str__(self):
        return "AB\t%s\t%s\t%s" % (self.da, self.db, self.duration)


# Precise V5 pens.
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
    pen_down_delay).
    """
    # FIXME actually do it
    return (100, 100)


def generate_moves(filename,
                   pen_up_position, pen_down_position,
                   colors=None, color_strategy='auto'):
    """
    Load an SVG file and render it to a list of moves.

    The ``colors`` argument is a sequence of available pens. If not supplied,
    it will default to a single black pen. The pens will be used in the order
    they supplied: e.g. a list like 'black', 'red', 'green' will assume that
    the plotter is first loaded with a black pen.

    The ``color_strategy`` argument determines how SVG geometry will be
    allocated to the available pens. The default is 'auto'.

        'auto': Uses actual path colors to assign geometry to pens by finding
        the closest color match.
        'layer': Uses layer names and looks for an exact match.

    NOTE: Colors are not really supported yet.
    """
    moves = []

    pen_up_delay, pen_down_delay = calculate_pen_delays(pen_up_position,
                                                        pen_down_position)

    tree = ElementTree.parse(filename)
    svg = tree.getroot()
    print(svg)

    moves.append(PenUpMove(pen_up_delay))
    moves.append(PenDownMove(pen_down_delay))
