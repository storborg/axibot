import logging

import sys
import argparse

import matplotlib.pyplot as plt

from axibot.svg import extract_paths


def render_paths(paths, subdivide=100):
    """
    Render a list of svg.path.Path instances to a matplotlib plot.
    """
    xdata = []
    ydata = []
    for path in paths:
        for n in range(subdivide):
            point = path.point(n / subdivide)
            xdata.append(point.real)
            ydata.append(point.imag)

    plt.plot(xdata, ydata, 'gs')
    plt.show()


def debug_paths(opts):
    paths = extract_paths(opts.filename)
    render_paths(paths)


def main(argv=sys.argv):
    p = argparse.ArgumentParser(description='Debug axibot software internals.')
    p.add_argument('--verbose', action='store_true')
    p.set_defaults(function=None)

    subparsers = p.add_subparsers(help='sub-command help')

    p_paths = subparsers.add_parser(
        'paths', help='Render normalized paths.')
    p_paths.add_argument('filename')
    p_paths.set_defaults(function=debug_paths)

    opts, args = p.parse_known_args(argv[1:])

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    if opts.function:
        return opts.function(opts)
    else:
        p.print_help()
