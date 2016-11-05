import os.path

from .. import svg

__here__ = os.path.dirname(__file__)
example_dir = os.path.join(__here__, '..', '..', 'examples')


def test_smoke():
    filename = os.path.join(example_dir, 'mixed.svg')
    paths = svg.extract_paths(filename)
    assert paths

    segments = svg.plan_segments(paths, smoothness=100)
    assert segments

    transits = svg.add_pen_transits(segments)
    assert transits
