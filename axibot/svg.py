import logging

from xml.etree import ElementTree

from . import moves

log = logging.getLogger(__name__)


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


def parse_transform(s):
    # XXX actually compute this
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


def path_to_moves(path, matrix):
    d = path.get('d')
    # XXX
    return []


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


def recurse_tree(actions, tree,
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
        # XXX
        matrix_new = matrix_current

        if node.tag == svgns('g'):
            recurse_tree(actions, node, matrix_new, parent_visibility=v,
                         plot_current_layer=plot_current_layer)
        elif node.tag == svgns('use'):
            raise NotImplementedError("we don't support the svg 'use' tag yet")
        elif plot_current_layer:
            if node.tag == svgns('path'):
                actions.extend(path_to_moves(node, matrix_new))
            elif node.tag in (svgns('rect'), svgns('line'), svgns('polyline'),
                              svgns('polygon'), svgns('ellipse'),
                              svgns('circle')):
                newpath = convert_to_path(node, matrix_new)
                actions.extend(path_to_moves(newpath, matrix_new))
            elif node.tag == svgns('text'):
                log.warn("Cannot directly draw text. Convert text to path.")
            elif node.tag == svgns('image'):
                log.warn("Cannot draw raster images. Vectorize first.")
            else:
                log.debug("Ignoring <%s> tag.", node.tag)


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

    doc = ElementTree.parse(filename)
    root = doc.getroot()

    svg_width, svg_height = get_document_properties(root)
    viewbox = root.get('viewBox')
    info = viewbox.strip().replace(',', ' ').split(' ')
    sx = svg_width / float(info[2])
    sy = svg_height / float(info[3])
    transform = parse_transform('scale(%f,%f) translate(%f,%f)' %
                                (sx, sy, -float(info[0]), -float(info[1])))

    # Always start with a pen up.
    actions.append(moves.PenUpMove(pen_up_delay))

    # Build list of actions.
    recurse_tree(actions, root, transform)

    # Always end with a pen up.
    actions.append(moves.PenUpMove(pen_up_delay))

    return actions
