import logging

import math

from xml.etree import ElementTree

from . import moves, config, planning

from .ext import (cspsubdiv, cubicsuperpath, simplepath, bezmisc,
                  simpletransform)

log = logging.getLogger(__name__)


def subdivide_cubic_path(sp, flat, i=1):
    """
    Initially taken from plot_utils.

    This should possibly be modified to return a new path rather than mutating
    the supplied one.

    Original docstring:

    Break up a bezier curve into smaller curves, each of which
    is approximately a straight line within a given tolerance
    (the "smoothness" defined by [flat]).

    This is a modified version of cspsubdiv.cspsubdiv(). I rewrote the
    recursive call because it caused recursion-depth errors on complicated line
    segments.
    """

    while True:
        while True:
            if i >= len(sp):
                return

            p0 = sp[i - 1][1]
            p1 = sp[i - 1][2]
            p2 = sp[i][0]
            p3 = sp[i][1]

            b = (p0, p1, p2, p3)

            if cspsubdiv.maxdist(b) > flat:
                break
            i += 1

        one, two = bezmisc.beziersplitatt(b, 0.5)
        sp[i - 1][2] = one[1]
        sp[i][0] = two[2]
        p = [one[2], one[3], two[1]]
        sp[i:1] = [p]


def get_length_inches(tree, name):
    s = tree.get(name)
    assert s
    s = s.strip()
    for unit in ('in', 'mm', 'cm'):
        if s[-2:] == unit:
            v = s[:-2]
            break
    else:
        raise ValueError("Couldn't understand units for %s" % tree)
    v = float(v)
    if unit == 'in':
        return v
    elif unit == 'mm':
        return v / 25.4
    elif unit == 'cm':
        return v / 2.54


def get_document_properties(tree):
    svg_width = get_length_inches(tree, 'width')
    svg_height = get_length_inches(tree, 'height')
    return svg_width, svg_height


def path_to_moves(start_position, path, transform_matrix, motion_config):
    """
    Generate the moves required to plot this path, while applying the
    supplied transformation matrix.

    Returns a tuple of (final_position, actions)

    Coordinates supplied to this function are absolute, and this function is
    responsible for computing any necessary moves to travel from last_position
    to the start point in the path.

    This is an analog to the legacy plotPath() function from the InkScape
    plugin.
    """
    d = path.get('d')

    print("-- start path_to_moves: %s" % d)

    if len(simplepath.parsePath(d)) == 0:
        # Skip empty paths
        return (start_position, [])

    p = cubicsuperpath.parsePath(d)

    # ...and apply the transformation to each point
    simpletransform.applyTransformToPath(transform_matrix, p)

    actions = []
    pos = start_position
    # p is now a list of lists of cubic beziers [control pt1, control pt2,
    # endpoint] where the start-point is the last point in the previous
    # segment.
    for sp in p:
        print("path_to_moves sp: %s" % sp)
        subdivide_cubic_path(sp, 0.02 / config.SMOOTHNESS)
        print("  subdivided: %s" % sp)
        n_index = 0

        single_path = []
        for csp in sp:
            fX = float(csp[1][0])  # Set move destination
            fY = float(csp[1][1])

            if n_index == 0:
                dx = fX - pos[0]
                dy = fY - pos[1]
                if math.sqrt((dx**2) + (dy**2)) > config.MIN_GAP:
                    actions.append(moves.PenUpMove(
                        motion_config['pen_up_delay']))
                    actions.extend(
                        planning.plot_segment_with_velocity((dx, dy), 0, 0,
                                                            pen_up=True))
            elif n_index == 1:
                actions.append(moves.PenDownMove(
                    motion_config['pen_down_delay']))
            n_index += 1

            single_path.append([fX, fY])

        pos = single_path[-1]
        print("  single_path %s" % single_path)
        traj_moves = planning.plan_trajectory(single_path, pen_up=False)
        actions.extend(traj_moves)

    for action in actions:
        print("     %s" % action)
    print("-- end path_to_moves: %s" % d)

    return (pos, actions)


def svgns(tag):
    return '{http://www.w3.org/2000/svg}' + tag


def convert_to_path(node, matrix):
    if node.tag == svgns('rect'):
        # transform a rect element into a path element
        newpath = ElementTree.Element('path')
        x = float(node.get('x'))
        y = float(node.get('y'))
        w = float(node.get('width'))
        h = float(node.get('height'))
        s = node.get('style')
        if s:
            newpath.set('style', s)
        t = node.get('transform')
        if t:
            newpath.set('transform', t)
        path = 'M{x},{y} l{w},0 l0,{h} l-{w},0 z'.format(x=x, y=y,
                                                         w=w, h=h)
        newpath.set('d', path)
        return newpath

    elif node.tag == svgns('line'):
        # transform a line element into a path element
        newpath = ElementTree.Element('path')
        x1 = float(node.get('x1'))
        y1 = float(node.get('y1'))
        x2 = float(node.get('x2'))
        y2 = float(node.get('y2'))
        s = node.get('style')
        if s:
            newpath.set('style', s)
        t = node.get('transform')
        if t:
            newpath.set('transform', t)
        path = 'M{x1},{y1} L{x2},{y2}'.format(x1=x1, y1=y1, x2=x2, y2=y2)
        newpath.set('d', path)
        return newpath

    elif node.tag == svgns('polyline'):
        raise NotImplementedError("doesn't support polyline yet")
    elif node.tag == svgns('polygon'):
        raise NotImplementedError("doesn't support polygon yet")
    elif node.tag == svgns('ellipse'):
        raise NotImplementedError("doesn't support ellipse yet")
    elif node.tag == svgns('circle'):
        raise NotImplementedError("doesn't support circle yet")
    else:
        raise ValueError("Don't know how to convert %s tag to a path." %
                         node.tag)


def recurse_tree(actions, last_position, tree, motion_config,
                 matrix_current=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                 parent_visibility='visible', plot_current_layer=True):
    for node in tree:
        log.debug("Handling element: %r: %r", node, node.items())

        # calculate node viz, ignore invisible nodes
        v = node.get('visibility', parent_visibility)
        if v == 'inherit':
            v = parent_visibility
        elif v == 'hidden' or v == 'collapse':
            pass

        # first apply current transform to this node's transform
        matrix_new = simpletransform.composeTransform(
            matrix_current,
            simpletransform.parseTransform(node.get('transform')))

        if node.tag == svgns('g'):
            last_position = recurse_tree(
                actions, last_position, node, motion_config,
                matrix_new,
                parent_visibility=v,
                plot_current_layer=plot_current_layer)
        elif node.tag == svgns('use'):
            raise NotImplementedError("we don't support the svg 'use' tag yet")
        elif plot_current_layer:
            if node.tag == svgns('path'):
                last_position, path_actions = path_to_moves(last_position,
                                                            node, matrix_new,
                                                            motion_config)
                actions.extend(path_actions)
            elif node.tag in (svgns('rect'), svgns('line'), svgns('polyline'),
                              svgns('polygon'), svgns('ellipse'),
                              svgns('circle')):
                newpath = convert_to_path(node, matrix_new)
                last_position, path_actions = path_to_moves(last_position,
                                                            newpath,
                                                            matrix_new,
                                                            motion_config)
                actions.extend(path_actions)
            elif node.tag == svgns('text'):
                log.warn("Cannot directly draw text. Convert text to path.")
            elif node.tag == svgns('image'):
                log.warn("Cannot draw raster images. Vectorize first.")
            else:
                log.debug("Ignoring <%s> tag.", node.tag)

    return last_position


def generate_actions(filename,
                     pen_up_position, pen_down_position,
                     colors=None, color_strategy='auto'):
    """
    Load an SVG file and render it to a list of actions.

    The ``colors`` argument is a sequence of available pens. If not supplied,
    it will default to a single black pen. The pens will be used in the order
    they supplied: e.g. a list like 'black', 'red', 'green' will assume that
    the plotter is first loaded with a black pen.

    The ``color_strategy`` argument determines how SVG geometry will be
    allocated to the available pens. The default is 'auto'.

        'auto': Uses actual path colors to assign geometry to pens by finding
        the closest color match.
        'layer': Uses layer names and looks for an exact match.

    NOTE: Colors are not supported yet, those arguments are ignored.

    FOOD FOR THOUGHT:

        - Should pen changes be a type of move? Or should they be some kind of
        nesting in the top-level data structure, so that it isn't just a plain
        list? Pen ordering is important, so it can't be an unordered dict.

        - Should there be any enforcement on homing/range?

        - Is it possible to at some point control multiple pens with the same
        AxiDraw (by adding more servos?)
    """
    actions = []

    pen_up_delay, pen_down_delay = \
        moves.calculate_pen_delays(pen_up_position, pen_down_position)
    motion_config = {
        'pen_up_delay': pen_up_delay,
        'pen_down_delay': pen_down_delay,
    }

    doc = ElementTree.parse(filename)
    root = doc.getroot()

    svg_width, svg_height = get_document_properties(root)
    viewbox = root.get('viewBox')
    info = viewbox.strip().replace(',', ' ').split(' ')
    sx = svg_width / float(info[2])
    sy = svg_height / float(info[3])
    transform = simpletransform.parseTransform(
        'scale(%f,%f) translate(%f,%f)' %
        (sx, sy, -float(info[0]), -float(info[1])))

    # Always start with a pen up.
    actions.append(moves.PenUpMove(pen_up_delay))

    # Build list of actions.
    start_position = 0, 0
    last_position = recurse_tree(actions, start_position, root, motion_config, transform)

    # Always end with a pen up and a move back to the start position.
    actions.append(moves.PenUpMove(pen_up_delay))
    dx = -last_position[0]
    dy = -last_position[1]
    actions.extend(planning.plot_segment_with_velocity((dx, dy), 0, 0,
                                                       pen_up=True))

    return actions
