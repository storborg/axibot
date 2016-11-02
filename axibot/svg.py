"""
New refactoring:

1. Recursively convert all segments into svg.path.Path objects while applying
transforms.

    This should result in a list of paths. It should be possible to render this
    to check for correctness.

    Unit testable functions:
        parse_transform(s) -> matrix
        compose_transform(matrix_current, matrix_new) -> matrix
        apply_transform(path, matrix) -> path

    Other functions:
        extract_paths(filename) -> list of (path, pen_up) tuples
        recurse_tree(paths, tree, transform) -> None, mutates paths in place

    Diagnostic functions:
        render_paths(paths)

2. Add pen-up transits?

2. Subdivide all paths into straight line segments, tracking pen state for each
segment.

    Ideally, we could put the 'smoothness' parameter into real units, so that
    it can be set more carefully based on the precision of the entire system
    (pen, paper, robot) and the perceptive limits of humans.

    Smoothness could be "max corner angle we are willing to tolerate along a
    bezier"?

    Note that at a certain point, increasing smoothness will necessarily
    decrease the speed, because if a line segment at full speed is shorter than
    the time slice (30ms), we need to slow down.

    Make sure we don't accumulate error here: straight-line segments have to
    start and end at round numbers of motor steps, but the start and end point
    of each path must not shift as a result. Compute the start and end point
    first, then make the last segment in the path just go straight to the end
    point.

    We might also want to do a least-squares fit of the subdivided segments to
    the original curve, but this could be quite computational intensive.

    This should result in a list of (((x0, y0), (x1, y1)), pen_up) tuples. It
    should be possible to render this to check for correctness.

    Unit testable functions:
        subdivide_path(path, smoothness)
            -> list of ((x0, y0), (x1, y1)) segments for path

    Other functions:
        plan_segments([list of (path, pen_up) tuples])
            -> list of (segment, pen_up) tuples

    Diagnostic functions:
        render_segments([list of (segment, pen_up) tuples])

3. For each corner point, compute max cornering velocity.

    The max cornering velocity should vary from the max speed for that pen
    state (faster for pen-up), for a trajectory change of 0 degrees, to zero,
    for a trajectory change of 180 degrees.

    This should result in a list of
    (((x0, y0), (x1, y1)), v_final, pen_up) tuples.

    Unit testable functions:
        cornering_angle((x0, y0), (x1, y1)) -> angle
        cornering_velocity(angle, pen_up) -> velocity

    Other functions:
        plan_corners(list of (segment, pen_up) tuples) -> list of tuples

    Diagnostic functions:
        render_corners([list of tuples])

4. For each segment, compute velocity profile and timeslices.

    This should result in a list of moves.

    ???

    Diagnostic functions:
        render_trajectory([list of moves])
"""

import logging

from xml.etree import ElementTree
from svg.path import parse_path

from . import transform

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


def svgns(tag):
    return '{http://www.w3.org/2000/svg}' + tag


def convert_to_path(node, matrix):
    if node.tag == svgns('rect'):
        # transform a rect element into a path
        x = float(node.get('x'))
        y = float(node.get('y'))
        w = float(node.get('width'))
        h = float(node.get('height'))
        return 'M{x},{y} l{w},0 l0,{h} l-{w},0 z'.format(x=x, y=y, w=w, h=h)

    elif node.tag == svgns('line'):
        # transform a line element into a path element
        x1 = float(node.get('x1'))
        y1 = float(node.get('y1'))
        x2 = float(node.get('x2'))
        y2 = float(node.get('y2'))
        return 'M{x1},{y1} L{x2},{y2}'.format(x1=x1, y1=y1, x2=x2, y2=y2)

    elif node.tag == svgns('polyline'):
        raise NotImplementedError("doesn't support polyline yet")
    elif node.tag == svgns('polygon'):
        raise NotImplementedError("doesn't support polygon yet")
    elif node.tag == svgns('ellipse') or node.tag == svgns('circle'):
        # Convert circles and ellipses to a path with two 180 degree arcs.
        # In general (an ellipse), we convert
        #   <ellipse rx="RX" ry="RY" cx="X" cy="Y"/>
        # to
        #   <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/>
        # where
        #   X1 = CX - RX
        #   X2 = CX + RX
        if node.tag == svgns('ellipse'):
            rx = float(node.get('rx', '0'))
            ry = float(node.get('ry', '0'))
        else:
            rx = float(node.get('r', '0'))
            ry = rx
        # XXX handle rx or ry of zero?

        cx = float(node.get('cx', '0'))
        cy = float(node.get('cy', '0'))
        x1 = cx - rx
        x2 = cx + rx
        return ('M %f,%f ' % (x1, cy) +
                'A %f,%f ' % (rx, ry) +
                '0 1 0 %f,%f ' % (x2, cy) +
                'A %f,%f ' % (rx, ry) +
                '0 1 0 %f,%f' % (x1, cy))
    else:
        raise ValueError("Don't know how to convert %s tag to a path." %
                         node.tag)


def process_path(s, transform_matrix):
    p = parse_path(s)
    transform.apply(p, transform_matrix)
    return p


def recurse_tree(paths, tree, transform_matrix, parent_visibility='visible'):
    """
    Append path tuples to the ``paths`` variable in place, while recursively
    parsing ``tree``.
    """
    for node in tree:
        log.debug("Handling element: %r: %r", node, node.items())

        # calculate node viz, ignore invisible nodes
        v = node.get('visibility', parent_visibility)
        if v == 'inherit':
            v = parent_visibility
        elif v == 'hidden' or v == 'collapse':
            pass

        # first apply current transform to this node's transform
        matrix_new = transform.compose(transform_matrix,
                                       transform.parse(node.get('transform')))

        if node.tag == svgns('g'):
            recurse_tree(paths, node, matrix_new, parent_visibility=v)
        elif node.tag == svgns('use'):
            raise NotImplementedError("we don't support the svg 'use' tag yet")
        elif node.tag == svgns('path'):
            paths.append(process_path(node.get('d'), matrix_new))
        elif node.tag in (svgns('rect'), svgns('line'), svgns('polyline'),
                          svgns('polygon'), svgns('ellipse'),
                          svgns('circle')):
            s = convert_to_path(node, matrix_new)
            paths.append(process_path(s, matrix_new))
        elif node.tag == svgns('text'):
            log.warn("Cannot directly draw text. Convert text to path.")
        elif node.tag == svgns('image'):
            log.warn("Cannot draw raster images. Vectorize first.")
        else:
            log.debug("Ignoring <%s> tag.", node.tag)


def extract_paths(filename):
    """
    Load an SVG file and convert it to a list of Path instances.
    """
    doc = ElementTree.parse(filename)
    root = doc.getroot()

    svg_width, svg_height = get_document_properties(root)
    viewbox = root.get('viewBox')
    info = viewbox.strip().replace(',', ' ').split(' ')
    sx = svg_width / float(info[2])
    sy = svg_height / float(info[3])
    matrix = transform.parse(
        'scale(%f,%f) translate(%f,%f)' %
        (sx, sy, -float(info[0]), -float(info[1])))

    paths = []
    recurse_tree(paths, root, matrix)
    return paths
