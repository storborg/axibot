import re
import math

from svg.path import Line, Arc, QuadraticBezier, CubicBezier


def parse(s, base=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]):
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


def apply_to_ellipse(rx, ry, ax, matrix):
    """
    Given an ellipse centered at 0, 0 defined by rx (x-radius), ry (y-radius),
    ax (angle x-axis is rotated), apply a transform matrix. Then return new rx,
    ry, ax.

    XXX this is most likely broken
    """
    epsilon = 0.0000000001
    m = [matrix[0][0], matrix[1][0], matrix[0][1], matrix[1][1]]
    torad = math.pi / 180

    c = math.cos(ax * torad)
    s = math.sin(ax * torad)

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
        rx = ry = math.sqrt(jk)
        ax = 0
        return rx, ry, ax

    l = ma[0] * ma[1] + ma[2] * ma[3]

    d = math.sqrt(d)
    l1 = jk + d / 2
    l2 = jk - d / 2

    if abs(l) < epsilon and abs(l1 - k) < epsilon:
        ax = 90
    elif abs(l) > abs(l1 - k):
        ax = math.atan((l1 - j) / l) * 180 / math.pi
    else:
        ax = math.atan(l / (l1 - k)) * 180 / math.pi

    if ax >= 0:
        rx = math.sqrt(l1)
        ry = math.sqrt(l2)
    else:
        ax += 90
        rx = math.sqrt(l2)
        ry = math.sqrt(l1)

    return rx, ry, ax


def apply(path, matrix):
    """
    Apply an affine transform to a Path instance.

    XXX this is broken for arcs
    """
    for piece in path:
        piece.start = apply_to_point(piece.start, matrix)
        piece.end = apply_to_point(piece.end, matrix)
        if isinstance(piece, Line):
            pass
        elif isinstance(piece, Arc):
            rx, ry, ax = apply_to_ellipse(piece.radius.real, piece.radius.imag,
                                          piece.rotation, matrix)
            print("%f %f %f" % (piece.radius.real, piece.radius.imag,
                                piece.rotation))
            print("   %r" % matrix)
            print("   %f %f %f" % (rx, ry, ax))

            if (matrix[0][0] * matrix[1][1] - matrix[1][0] * matrix[0][1]) < 0:
                piece.sweep = not piece.sweep

            # XXX handle empty arcs or degenerate (flattened) arcs here?

            piece.radius = complex(rx, ry)
            piece.rotation = ax
        elif isinstance(piece, QuadraticBezier):
            piece.control1 = apply_to_point(piece.control1, matrix)
        elif isinstance(piece, CubicBezier):
            piece.control1 = apply_to_point(piece.control1, matrix)
            piece.control2 = apply_to_point(piece.control2, matrix)
        else:
            raise ValueError("Don't know how to transform %r" % piece)
