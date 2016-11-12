from pprint import pprint
from unittest import TestCase

from .. import planning


class TestVelocityProfile(TestCase):

    def test_basic_trapezoid(self):
        xdiff = 4064
        xstart = 1247

        start = (xstart, 0)
        vstart = 0
        end = (xstart + xdiff, 0)
        vend = 0
        pen_up = False

        dtarray = planning.interpolate_pair(start, vstart, end, vend, pen_up)
        total_dist = dtarray[-1][0]
        self.assertEqual(xdiff, total_dist)

    def test_basic_triangular(self):
        start = (1032, 1992)
        vstart = 0
        end = (9079, 15167)
        vend = 0
        pen_up = True
        dist = planning.distance(start, end)
        dtarray = planning.interpolate_pair(start, vstart, end, vend, pen_up)
        total_dist = dtarray[-1][0]
        self.assertEqual(dist, total_dist)

    def test_basic_linear(self):
        start = (4500, 5200)
        end = (4680, 5050)
        dist = planning.distance(start, end)
        dtarray = planning.interpolate_pair(start, 6000, end, 6200, True)
        total_dist = dtarray[-1][0]
        self.assertEqual(dist, total_dist)
