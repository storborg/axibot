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
