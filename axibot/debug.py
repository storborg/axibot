import logging

import sys
import argparse

import matplotlib.pyplot as plt

from axibot import svg


def debug_paths(opts):
    """
    Render an SVG file into paths, and then plot them with matplotlib.
    """
    subdivide = 100
    paths = svg.extract_paths(opts.filename)
    for path in paths:
        xdata = []
        ydata = []
        for n in range(subdivide):
            point = path.point(n / subdivide)
            xdata.append(point.real)
            ydata.append(-point.imag)
        plt.plot(xdata, ydata, 'g-')

    plt.show()


def debug_segments(opts):
    """
    Render an SVG file into linear segments, and then plot them with matplotlib.
    """
    smoothness = 10
    paths = svg.extract_paths(opts.filename)
    segments = svg.plan_segments(paths, smoothness=smoothness)

    xdata = []
    ydata = []

    for segment in segments:
        for (x, y) in segment:
            xdata.append(x)
            ydata.append(-y)

    plt.plot(xdata, ydata, 'g-')
    plt.show()


def debug_transits(opts):
    smoothness = 10
    paths = svg.extract_paths(opts.filename)
    segments = svg.plan_segments(paths, smoothness=smoothness)
    transits = svg.add_pen_transits(segments)

    for segment, pen_up in transits:
        xdata = []
        ydata = []
        for (x, y) in segment:
            xdata.append(x)
            ydata.append(-y)
        plt.plot(xdata, ydata, 'r-' if pen_up else 'g-')

    plt.show()


def main(argv=sys.argv):
    p = argparse.ArgumentParser(description='Debug axibot software internals.')
    p.add_argument('--verbose', action='store_true')
    p.set_defaults(function=None)

    subparsers = p.add_subparsers(help='sub-command help')

    p_paths = subparsers.add_parser(
        'paths', help='Render normalized paths.')
    p_paths.add_argument('filename')
    p_paths.set_defaults(function=debug_paths)

    p_segments = subparsers.add_parser(
        'segments', help='Render linear segments.')
    p_segments.add_argument('filename')
    p_segments.set_defaults(function=debug_segments)

    p_transits = subparsers.add_parser(
        'transits', help='Render segments with pen transits.')
    p_transits.add_argument('filename')
    p_transits.set_defaults(function=debug_transits)

    opts, args = p.parse_known_args(argv[1:])

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    if opts.function:
        return opts.function(opts)
    else:
        p.print_help()
