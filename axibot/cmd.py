import logging

import sys
import argparse

from .moves import render
from .ebb import EiBotBoard


def debug(opts):
    print("Rendering %s..." % opts.filename)
    render(opts.filename)


def manual_up(opts):
    # manually move pen up
    bot = EiBotBoard.find()
    bot.pen_up()


def manual_down(opts):
    # manually move pen down
    bot = EiBotBoard.find()
    bot.pen_down()


def plot(opts):
    print("Loading %s..." % opts.filename)
    bot = EiBotBoard.find()


def server(opts):
    print("Serving on port %d..." % opts.port)
    bot = EiBotBoard.find()


def main(args=sys.argv):
    p = argparse.ArgumentParser(description='Print with the AxiDraw.')
    p.add_argument('--verbose', action='store_true')
    p.set_defaults(function=None)

    subparsers = p.add_subparsers(help='sub-command help')

    p_debug = subparsers.add_parser(
        'debug', help='Debug info about an SVG file rendering.')
    p_debug.add_argument('filename')
    p_debug.set_defaults(function=debug)

    p_plot = subparsers.add_parser(
        'plot', help='Plot an SVG file directly.')
    p_plot.add_argument('filename')
    p_plot.set_defaults(function=plot)

    p_server = subparsers.add_parser(
        'server', help='Run a server for remote plotting.')
    p_server.add_argument('--port', type=int, default=8888)
    p_server.set_defaults(function=server)

    p_manual_up = subparsers.add_parser(
        'up', help='Lift pen up.')
    p_manual_up.set_defaults(function=manual_up)

    p_manual_down = subparsers.add_parser(
        'down', help='Drop pen down.')
    p_manual_down.set_defaults(function=manual_down)

    opts, args = p.parse_known_args(args[1:])

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    if opts.function:
        return opts.function(opts)
    else:
        p.print_help()
