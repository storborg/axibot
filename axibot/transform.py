from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import re
import math

from svg.path import Line, Arc, QuadraticBezier, CubicBezier


identity = [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]]


def _flatten(mat):
    """
    Convert array format:
        [[A, C, E],
         [B, D, F]]
         ->
        [A, B, C, D, E, F]
    """
    return [mat[0][0], mat[1][0], mat[0][1], mat[1][1], mat[0][2], mat[1][2]]


def parse(s, base=identity):
    """
    Parse SVG transform syntax into a 2x3 affine transform matrix.
    """
    s = (s or "").strip()
    if not s:
        return base

    m = re.match(
        "(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]*)\)\s*,?",
        s)

    cmd = m.group(1)
    val = m.group(2)

    if cmd == "translate":
        args = val.replace(',', ' ').split()
        dx = float(args[0])
        if len(args) == 1:
            dy = 0.0
        else:
            dy = float(args[1])
        matrix = [[1, 0, dx], [0, 1, dy]]

    elif cmd == "scale":
        args = val.replace(',', ' ').split()
        sx = float(args[0])
        if len(args) == 1:
            sy = sx
        else:
            sy = float(args[1])
        matrix = [[sx, 0, 0], [0, sy, 0]]

    elif cmd == "rotate":
        args = val.replace(',', ' ').split()
        a = float(args[0]) * math.pi / 180
        if len(args) == 1:
            cx, cy = (0.0, 0.0)
        else:
            cx, cy = map(float, args[1:])
        matrix = [[math.cos(a), -math.sin(a), cx],
                  [math.sin(a), math.cos(a), cy]]
        matrix = compose(matrix, [[1, 0, -cx], [0, 1, -cy]])

    elif cmd == "skewX":
        a = float(val) * math.pi / 180
        matrix = [[1, math.tan(a), 0], [0, 1, 0]]

    elif cmd == "skewY":
        a = float(val) * math.pi / 180
        matrix = [[1, 0, 0], [math.tan(a), 1, 0]]

    elif cmd == "matrix":
        a11, a21, a12, a22, v1, v2 = val.replace(',', ' ').split()
        matrix = [[float(a11), float(a12), float(v1)],
                  [float(a21), float(a22), float(v2)]]

    matrix = compose(base, matrix)
    if m.end() < len(s):
        return parse(s[m.end():], matrix)
    else:
        return matrix


def compose(mbase, mnew):
    """
    Compose a new affine transform matrix based on an existing one and a new
    one.
    """
    a11 = mbase[0][0] * mnew[0][0] + mbase[0][1] * mnew[1][0]
    a12 = mbase[0][0] * mnew[0][1] + mbase[0][1] * mnew[1][1]
    a21 = mbase[1][0] * mnew[0][0] + mbase[1][1] * mnew[1][0]
    a22 = mbase[1][0] * mnew[0][1] + mbase[1][1] * mnew[1][1]

    v1 = mbase[0][0] * mnew[0][2] + mbase[0][1] * mnew[1][2] + mbase[0][2]
    v2 = mbase[1][0] * mnew[0][2] + mbase[1][1] * mnew[1][2] + mbase[1][2]
    return [[a11, a12, v1], [a21, a22, v2]]


def apply_to_point(pt, matrix):
    """
    Apply a 2x3 affine transform matrix to a point.
    """
    x = matrix[0][0] * pt.real + matrix[0][1] * pt.imag + matrix[0][2]
    y = matrix[1][0] * pt.real + matrix[1][1] * pt.imag + matrix[1][2]
    return complex(x, y)


def apply_to_ellipse(rx, ry, ax, m):
    """
    Given an ellipse centered at 0, 0 defined by rx (x-radius), ry (y-radius),
    ax (angle x-axis is rotated), apply a flattened transform matrix. Then
    return new rx, ry, ax.
    """
    epsilon = 0.0000000001

    c = math.cos(math.radians(ax))
    s = math.sin(math.radians(ax))

    ma = [rx * (m[0] * c + m[2] * s),
          rx * (m[1] * c + m[3] * s),
          ry * (-m[0] * s + m[2] * c),
          ry * (-m[1] * s + m[3] * c)]

    j = ma[0] * ma[0] + ma[2] * ma[2]
    k = ma[1] * ma[1] + ma[3] * ma[3]

    d = (((ma[0] - ma[3]) * (ma[0] - ma[3]) +
          (ma[2] + ma[1]) * (ma[2] + ma[1])) *
         ((ma[0] + ma[3]) * (ma[0] + ma[3]) +
          (ma[2] - ma[1]) * (ma[2] - ma[1])))

    jk = (j + k) / 2

    if (d < epsilon * jk):
        new_rx = new_ry = math.sqrt(jk)
        new_ax = 0
        return new_rx, new_ry, new_ax

    l = ma[0] * ma[1] + ma[2] * ma[3]

    d = math.sqrt(d)

    l1 = jk + d / 2
    l2 = jk - d / 2

    if abs(l) < epsilon and abs(l1 - k) < epsilon:
        new_ax = 90
    else:
        if abs(l) > abs(l1 - k):
            new_ax = math.degrees(math.atan((l1 - j) / l))
        else:
            new_ax = math.degrees(math.atan(l / (l1 - k)))

    if ax >= 0:
        new_rx = math.sqrt(l1)
        new_ry = math.sqrt(l2)
    else:
        new_ax += 90
        new_rx = math.sqrt(l2)
        new_ry = math.sqrt(l1)

    return new_rx, new_ry, new_ax


def apply(path, matrix):
    """
    Apply an affine transform to a Path instance.

    XXX this is broken for arcs
    """
    for piece in path:
        if isinstance(piece, Line):
            piece.start = apply_to_point(piece.start, matrix)
            piece.end = apply_to_point(piece.end, matrix)
        elif isinstance(piece, Arc):
            ma = _flatten(matrix)
            rx, ry, ax = apply_to_ellipse(
                piece.radius.real,
                piece.radius.imag,
                piece.rotation,
                ma)
            if ma[0] * ma[3] - ma[1] * ma[2] < 0:
                piece.sweep = not piece.sweep
            piece.start = apply_to_point(piece.start, matrix)
            piece.end = apply_to_point(piece.end, matrix)
            piece.center = apply_to_point(piece.center, matrix)
            piece.radius = complex(rx, ry)
            piece.rotation = ax
        elif isinstance(piece, QuadraticBezier):
            piece.start = apply_to_point(piece.start, matrix)
            piece.end = apply_to_point(piece.end, matrix)
            piece.control = apply_to_point(piece.control, matrix)
        elif isinstance(piece, CubicBezier):
            piece.start = apply_to_point(piece.start, matrix)
            piece.end = apply_to_point(piece.end, matrix)
            piece.control1 = apply_to_point(piece.control1, matrix)
            piece.control2 = apply_to_point(piece.control2, matrix)
        else:
            raise ValueError("Don't know how to transform %r" % piece)
