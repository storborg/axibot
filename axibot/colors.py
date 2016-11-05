from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import math
from operator import itemgetter

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color


pen_sets = {
    'precise-v5': {
        'black': (59, 59, 59),
        'blue': (61, 93, 134),
        'red': (138, 56, 60),
        'green': (52, 126, 101),
        'purple': (93, 90, 179),
        'lightblue': (69, 153, 189),
        'pink': (225, 87, 146),
    }
}


def rgb_to_lab(rgb):
    rgb_color = sRGBColor(rgb[0], rgb[1], rgb[2])
    lab_color = convert_color(rgb_color, LabColor)
    return lab_color.lab_l, lab_color.lab_a, lab_color.lab_b


def perceptual_distance(a, b):
    a = rgb_to_lab(a)
    b = rgb_to_lab(b)
    return math.sqrt((b[2] - a[2])**2 +
                     (b[1] - a[1])**2 +
                     (b[0] - a[0])**2)


def find_pen_match(color, pen_set):
    scores = {}
    for pen, pen_color in pen_sets[pen_set].items():
        scores[pen] = perceptual_distance(color, pen_color)
    scores = scores.items()
    scores.sort(key=itemgetter(1))
    return scores[0]
