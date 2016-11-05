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

2. Subdivide all paths into straight line segments.

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

    Unit testable functions:
        subdivide_path(path, smoothness)
            -> list of ((x0, y0), (x1, y1)) segments for path

    Other functions:
        plan_segments([list of paths])
            -> list of [list of points]

    Diagnostic functions:
        render_segments([list of segment lists])

3. For each point, compute max cornering velocity in and out of that
point, adding pen-up transits that start and stop at zero velocity.

    The max cornering velocity should vary from the max speed for that pen
    state (faster for pen-up), for a trajectory change of 0 degrees, to zero,
    for a trajectory change of 180 degrees.

    This should result in a list of
    (((x0, y0), (x1, y1)), v_final, pen_up) tuples.

    Unit testable functions:
        cornering_angle((x0, y0), (x1, y1)) -> angle
        cornering_velocity(angle, pen_up) -> velocity

    Other functions:
        plan_speed_limits(list of (segment, pen_up) tuples) -> list of tuples

    Diagnostic functions:
        render_corners([list of tuples])

4. For each segment, compute velocity profile and timeslices.

    This should result in a list of moves.

    Unit-testable functions:
        plan_segment_velocity(start, end, v_initial, v_final, pen_up)
            -> list of moves

    Other functions:
        plan_moves([list of (start, end, v_final, pen_up_to) tuples])
            -> list of moves

    Diagnostic functions:
        render_trajectory([list of moves])
"""

import logging

import math

from xml.etree import ElementTree
from svg.path import parse_path, Line

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


def subdivide_path(path, smoothness):
    """
    Given a svg.path.Path instance, output a list of points to traverse. The
    ``smoothness`` parameter specifies how smooth the curve approximation
    should be.

    XXX the 'smoothness' parameter sucks right now and should be made better.
    """
    points = []
    for piece in path:
        if isinstance(piece, Line):
            # Don't subdivide lines.
            points.append((piece.start.real, piece.start.imag))
            points.append((piece.end.real, piece.end.imag))
        else:
            for n in range(smoothness + 1):
                point = piece.point(n / smoothness)
                points.append((point.real, point.imag))
    return points


def plan_segments(paths, smoothness):
    """
    Takes a list of Path instances, returns a list of lists of points.
    """
    return [subdivide_path(path, smoothness) for path in paths]


def join_segments(segments, min_gap):
    """
    Takes a list of segments (which are lists of points) and joins them when
    the start of one segment is within a certain tolerance of the end of the
    previous segment.

    XXX this needs to actually get called, maybe. Not sure it helps.
    """
    if len(segments) < 2:
        return segments
    last_segment = segments[0]
    new_segments = [last_segment]
    for segment in segments[1:]:
        x0, y0 = last_segment[-1]
        x1, y1 = segment[0]
        if math.sqrt((x1 - x0)**2 + (y1 - y0)**2) < min_gap:
            last_segment.extend(segment)
        else:
            last_segment = segment
            new_segments.append(segment)
    return new_segments


def add_pen_transits(segments):
    """
    Takes a list of pen-down segments. Returns a list of (segment, pen_up)
    tuples, with additional segments added that pen-up transit between
    segments. Also add segments at the beginning and end to transit the pen
    from and to the origin location.

    The output list should thus always have 2n+1 elements, where n is the
    length of the input list.
    """
    assert segments
    origin = 0, 0

    out_segments = []
    start_seg = [origin, segments[0][0]]
    out_segments.append((start_seg, True))

    count = len(segments)

    for n, seg in enumerate(segments, start=1):
        out_segments.append((seg, False))
        if n == count:
            # last one
            next_seg_start = origin
        else:
            next_seg_start = segments[n][0]
        transit_seg = [seg[-1], next_seg_start]
        out_segments.append((transit_seg, True))

    return out_segments


def transform_path(s, transform_matrix):
    """
    Parse the path described by string ``s`` and apply the transform matrix.
    """
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
        print("matrix %r" % matrix_new)

        if node.tag == svgns('g'):
            recurse_tree(paths, node, matrix_new, parent_visibility=v)
        elif node.tag == svgns('use'):
            raise NotImplementedError("we don't support the svg 'use' tag yet")
        elif node.tag == svgns('path'):
            paths.append(transform_path(node.get('d'), matrix_new))
        elif node.tag in (svgns('rect'), svgns('line'), svgns('polyline'),
                          svgns('polygon'), svgns('ellipse'),
                          svgns('circle')):
            s = convert_to_path(node, matrix_new)
            paths.append(transform_path(s, matrix_new))
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
