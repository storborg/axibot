import logging

import sys
import argparse

import matplotlib.pyplot as plt

from axibot import svg, planning, config


def show(opts):
    if opts.out:
        plt.savefig(opts.out, dpi=300)
    else:
        plt.show()


def debug_paths(opts):
    """
    Render an SVG file into paths, and then plot them with matplotlib.
    """
    subdivide = 100
    paths = svg.extract_paths(opts.filename)
    for path in paths:
        xdata = []
        ydata = []
        for n in range(subdivide + 1):
            point = path.point(n / subdivide)
            xdata.append(point.real)
            ydata.append(-point.imag)
        plt.plot(xdata, ydata, 'g-')

    show(opts)


def debug_segments(opts):
    """
    Render an SVG file into linear segments, and then plot them with
    matplotlib.
    """
    smoothness = 100
    paths = svg.extract_paths(opts.filename)
    segments = svg.plan_segments(paths, smoothness=smoothness)

    xdata = []
    ydata = []

    for segment in segments:
        for (x, y) in segment:
            xdata.append(x)
            ydata.append(-y)

    plt.plot(xdata, ydata, 'g-')
    show(opts)


def debug_transits(opts):
    smoothness = 100
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

    show(opts)


def debug_corners(opts):
    smoothness = 10
    paths = svg.extract_paths(opts.filename)
    segments = svg.plan_segments(paths, smoothness=smoothness)
    transits = svg.add_pen_transits(segments)
    segments_limits = planning.plan_speed_limits(transits)

    up_xdata = []
    up_ydata = []
    up_speed = []
    down_xdata = []
    down_ydata = []
    down_speed = []

    def speed_to_opacity(speed, limit, min_opacity=0.2):
        opacity = speed / limit
        if opacity < min_opacity:
            return min_opacity
        elif opacity > 1.0:
            return 1.0
        else:
            return opacity

    def speed_to_color(speed, pen_up):
        if pen_up:
            return (1.0, 0.0, 0.0,
                    speed_to_opacity(speed, config.SPEED_PEN_UP))
        else:
            return (0.0, 0.1, 0.0,
                    speed_to_opacity(speed, config.SPEED_PEN_DOWN))

    def record_point(point, vmax, pen_up):
        x, y = point
        y = -y
        if pen_up:
            up_xdata.append(x)
            up_ydata.append(y)
            up_speed.append(speed_to_color(vmax, pen_up))
        else:
            down_xdata.append(x)
            down_ydata.append(y)
            down_speed.append(speed_to_color(vmax, pen_up))

    init_segment = segments_limits[0]
    record_point(init_segment[0], init_segment[2], init_segment[4])

    for start, end, start_vmax, end_vmax, pen_up in segments_limits:
        xdata = [start[0], end[0]]
        ydata = [-start[1], -end[1]]
        record_point(end, end_vmax, pen_up)
        plt.plot(xdata, ydata, 'r-' if pen_up else 'g-')

    plt.scatter(up_xdata, up_ydata, s=50, linewidths=0, c=up_speed)
    plt.scatter(down_xdata, down_ydata, s=50, linewidths=0, c=down_speed)

    show(opts)


def main(argv=sys.argv):
    p = argparse.ArgumentParser(description='Debug axibot software internals.')
    p.add_argument('--verbose', action='store_true')
    p.set_defaults(function=None)

    subparsers = p.add_subparsers(help='sub-command help')

    p_paths = subparsers.add_parser(
        'paths', help='Render normalized paths.')
    p_paths.add_argument('filename')
    p_paths.add_argument('--out')
    p_paths.set_defaults(function=debug_paths)

    p_segments = subparsers.add_parser(
        'segments', help='Render linear segments.')
    p_segments.add_argument('filename')
    p_segments.add_argument('--out')
    p_segments.set_defaults(function=debug_segments)

    p_transits = subparsers.add_parser(
        'transits', help='Render segments with pen transits.')
    p_transits.add_argument('filename')
    p_transits.add_argument('--out')
    p_transits.set_defaults(function=debug_transits)

    p_corners = subparsers.add_parser(
        'corners', help='Render points with speeds.')
    p_corners.add_argument('filename')
    p_corners.add_argument('--out')
    p_corners.set_defaults(function=debug_corners)

    opts, args = p.parse_known_args(argv[1:])

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    if opts.function:
        return opts.function(opts)
    else:
        p.print_help()
