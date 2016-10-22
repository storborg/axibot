class Move:
    pass


class PenUpMove(Move):
    pass


class PenDownMove(Move):
    pass


class XYMove(Move):
    pass


class XYAccelMove(Move):
    pass


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


def render(filename, colors=None, color_strategy='auto'):
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
    """
    pass
