import re
import math

from svg.path import Line, Arc, QuadraticBezier, CubicBezier


def parse(s, base=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]):
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
    a11 = mbase[0][0] * mnew[0][0] + mbase[0][1] * mnew[1][0]
    a12 = mbase[0][0] * mnew[0][1] + mbase[0][1] * mnew[1][1]
    a21 = mbase[1][0] * mnew[0][0] + mbase[1][1] * mnew[1][0]
    a22 = mbase[1][0] * mnew[0][1] + mbase[1][1] * mnew[1][1]

    v1 = mbase[0][0] * mnew[0][2] + mbase[0][1] * mnew[1][2] + mbase[0][2]
    v2 = mbase[1][0] * mnew[0][2] + mbase[1][1] * mnew[1][2] + mbase[1][2]
    return [[a11, a12, v1], [a21, a22, v2]]


def apply_to_point(pt, matrix):
    x = matrix[0][0] * pt.real + matrix[0][1] * pt.imag + matrix[0][2]
    y = matrix[1][0] * pt.real + matrix[1][1] * pt.imag + matrix[1][2]
    return complex(x, y)


def apply(path, matrix):
    for piece in path:
        piece.start = apply_to_point(piece.start, matrix)
        piece.end = apply_to_point(piece.end, matrix)
        if isinstance(piece, Line):
            pass
        elif isinstance(piece, Arc):
            raise NotImplementedError
        elif isinstance(piece, QuadraticBezier):
            piece.control1 = apply_to_point(piece.control1, matrix)
        elif isinstance(piece, CubicBezier):
            piece.control1 = apply_to_point(piece.control1, matrix)
            piece.control2 = apply_to_point(piece.control2, matrix)
        else:
            raise ValueError("Don't know how to transform %r" % piece)
