from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os.path

from .. import svg, config

__here__ = os.path.dirname(__file__)
example_dir = os.path.join(__here__, '..', '..', 'examples')


def test_smoke():
    filename = os.path.join(example_dir, 'mixed.svg')
    with open(filename) as f:
        paths = svg.extract_paths(f.read())
    assert paths

    segments = svg.plan_segments(paths, resolution=config.CURVE_RESOLUTION)
    assert segments

    segments = svg.add_pen_up_moves(segments)
    assert segments
