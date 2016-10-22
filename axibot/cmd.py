import logging

import sys
import argparse

from .svg import generate_moves
from .ebb import EiBotBoard


def debug(opts):
    print("Rendering %s..." % opts.filename)
    moves = generate_moves(
        opts.filename,
        pen_up_position=85,
        pen_down_position=35,
    )
    for move in moves:
        print(move)


def manual_up(opts):
    # manually move pen up
    bot = EiBotBoard.find()
    try:
        bot.pen_up()
    finally:
        bot.close()


def manual_down(opts):
    # manually move pen down
    bot = EiBotBoard.find()
    try:
        bot.pen_down()
    finally:
        bot.close()


def manual_off(opts):
    # lift pen and turn motors off
    bot = EiBotBoard.find()
    try:
        bot.pen_up()
        bot.disable_motors()
    finally:
        bot.close()


def plot(opts):
    print("Loading %s..." % opts.filename)
    bot = EiBotBoard.find()

    # XXX find pen positions with user interaction?
    pen_up_position = 85
    pen_down_position = 50

    try:
        moves = generate_moves(
            opts.filename,
            pen_up_position=pen_up_position,
            pen_down_position=pen_down_position,
        )
        count = len(moves)
        print("Calculated %d moves." % count)

        bot.pen_up()
        bot.disable_motors()
        print("Pen up and motors off. Move carriage to top left corner.")
        input("Press enter to begin.")

        for ii, move in enumerate(moves):
            print("Move %d/%d" % (ii, count))
            bot.do(move)

        bot.pen_up()
        print("Finished!")
    finally:
        bot.close()


def server(opts):
    print("Serving on port %d..." % opts.port)
    bot = EiBotBoard.find()
    try:
        raise NotImplementedError
    finally:
        bot.close()


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

    p_manual_off = subparsers.add_parser(
        'off', help='Turn motors off and lift pen.')
    p_manual_off.set_defaults(function=manual_off)

    opts, args = p.parse_known_args(args[1:])

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    if opts.function:
        return opts.function(opts)
    else:
        p.print_help()
