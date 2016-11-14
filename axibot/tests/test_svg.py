from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os.path

from .. import svg, config

__here__ = os.path.dirname(__file__)
example_dir = os.path.join(__here__, '..', '..', 'examples')


def test_smoke():
    filename = os.path.join(example_dir, 'mixed.svg')
    paths = svg.extract_paths(filename)
    assert paths

    segments = svg.plan_segments(paths, resolution=config.CURVE_RESOLUTION)
    assert segments

    transits = svg.add_pen_transits(segments)
    assert transits
