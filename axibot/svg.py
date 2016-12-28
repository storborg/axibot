from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging

import math

from xml.etree import ElementTree
from svg.path import parse_path, Path, Line

from . import transform

log = logging.getLogger(__name__)


def convert_to_inches(s):
    """
    Convert an SVG unit string like '42.5mm' or '12in' to inches as a float. If
    the unit string does not include physical units, return None.
    """
    assert s
    s = s.strip()
    for unit in ('in', 'mm', 'cm'):
        if s[-2:] == unit:
            v = s[:-2]
            break
    else:
        return None
    v = float(v)
    if unit == 'in':
        return v
    elif unit == 'mm':
        return v / 25.4
    elif unit == 'cm':
        return v / 2.54


def parse_pixels(s):
    # Both px and pt are effectively unitless?
    if s.endswith('px') or s.endswith('pt'):
        s = s[:-2]
    return float(s)


def get_viewbox_dimensions(viewbox):
    viewbox_fields = viewbox.strip().replace(',', ' ').split(' ')
    sx, sy, w, h = viewbox_fields
    return w, h


def get_document_dimensions(tree, max_area=(11, 8.5)):
    """
    Return the dimensions of this document in inches as to be plotted. If the
    document specifies physical units, they will be converted to inches, and
    asserted to be less than the working area of the AxiDraw. If the document
    does not specify physical units (e.g. the width and height are in pixels
    only) it will be scaled to the working area.

    Returns a tuple of (width, height) in inches.
    """
    max_width, max_height = max_area
    raw_width = tree.get('width')
    raw_height = tree.get('height')
    if not (raw_width and raw_height):
        log.warn("This document does not have width and height attributes. "
                 "Extracting viewbox dimensions.")
        svg_width = svg_height = None
        raw_width, raw_height = get_viewbox_dimensions(tree.get('viewBox'))
    else:
        svg_width = convert_to_inches(raw_width)
        svg_height = convert_to_inches(raw_height)
    if not (svg_width and svg_height):
        log.warn("This document does not specify physical units. "
                 "Auto-scaling it to fit the drawing area.")
        width = parse_pixels(raw_width)
        height = parse_pixels(raw_height)
        aspect_ratio = width / height
        max_ratio = max_width / max_height
        if aspect_ratio > max_ratio:
            # Wider than working area, constrained by width
            scale = max_width / width
        else:
            # Taller than working area, constrained by height
            scale = max_height / height
        svg_width = scale * width
        svg_height = scale * height
    assert svg_width <= max_width, \
        "SVG width of %s must be <= %s" % (svg_width, max_width)
    assert svg_height <= max_height, \
        "SVG height of %s must be <= %s" % (svg_height, max_height)
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


def subdivide_path(path, resolution):
    """
    Given a svg.path.Path instance, output a list of points to traverse. The
    ``smoothness`` parameter specifies how smooth the curve approximation
    should be.

    Note that typical "full speed" distance per timeslice is around 0.37".
    """
    points = []
    for piece in path:
        if isinstance(piece, Line):
            # Don't subdivide lines.
            points.append((piece.start.real, piece.start.imag))
            points.append((piece.end.real, piece.end.imag))
        else:
            dist = piece.length(error=1e-6)
            count = int(math.ceil(dist / resolution))
            for n in range(count + 1):
                point = piece.point(n / count)
                points.append((point.real, point.imag))
    return points


def plan_segments(paths, resolution):
    """
    Takes a list of Path instances, returns a list of lists of points.
    """
    return [subdivide_path(path, resolution) for path in paths]


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


def add_pen_up_moves(segments):
    """
    Takes a list of pen-down segments. Returns a list of (segment, pen_up)
    tuples, with additional segments added that pen-up move between segments.
    Also add segments at the beginning and end to do pen-up moves from and to
    the origin location.

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
        assert seg
        out_segments.append((seg, False))
        if n == count:
            # last one
            next_seg_start = origin
        else:
            next_seg_start = segments[n][0]
        inter_seg = [seg[-1], next_seg_start]
        out_segments.append((inter_seg, True))

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


def extract_paths(s):
    root = ElementTree.fromstring(s)
    # Check if the svg element has the correct namespace
    if not root.tag.startswith('{http://www.w3.org/2000/svg}'):
        log.warn("File is invalid, missing svg namespace declaration")
        raise RuntimeError("File is invalid, missing svg namespace declaration")

    svg_width, svg_height = get_document_dimensions(root)
    viewbox = root.get('viewBox')

    if viewbox:
        info = viewbox.strip().replace(',', ' ').split(' ')
        sx = svg_width / float(info[2])
        sy = svg_height / float(info[3])
        tx = -float(info[0])
        ty = -float(info[1])
    else:
        sx = sy = 1
        tx = ty = 0

    matrix = transform.parse(
        'scale(%f,%f) translate(%f,%f)' %
        (sx, sy, tx, ty))

    paths = []
    recurse_tree(paths, root, matrix)
    return paths


def split_disconnected_paths(paths):
    """
    Accepts a list of Path instances. Iterates over paths to determine if
    adjacent sections are actually connected. If they are not, the paths are
    split into multiple Path instances so that each instance contains only
    connected paths.
    """
    out_paths = []
    for path in paths:
        new_path = Path()
        last_point = path[0].start
        for section in path:
            if section.start != last_point:
                out_paths.append(new_path)
                new_path = Path()
            last_point = section.end
            new_path.append(section)
        out_paths.append(new_path)
    return out_paths


def distance_squared(a, b):
    return ((b.real - a.real)**2) + ((b.imag - a.imag)**2)


def find_closest_path(current_point, paths):
    best_score = None
    best_path = None
    for path in paths:
        score = distance_squared(current_point, path[0].start)
        if (not best_score) or (score < best_score):
            best_score = score
            best_path = path
    return best_path


def sort_paths(paths):
    """
    Sort list of paths by start point. This is a crude heuristic to try to
    avoid spending as much time moving around with the pen up.
    """
    out_paths = []
    current_point = complex(0, 0)
    while paths:
        next_path = find_closest_path(current_point, paths)
        current_point = next_path[-1].end
        paths.remove(next_path)
        out_paths.append(next_path)
    return out_paths


def preprocess_paths(paths):
    paths = split_disconnected_paths(paths)
    paths = sort_paths(paths)
    return paths
