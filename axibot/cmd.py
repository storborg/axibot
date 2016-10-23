import logging

import sys
import argparse

from . import moves
from .svg import generate_actions
from .ebb import EiBotBoard


def debug(opts):
    print("Rendering %s..." % opts.filename)
    actions = generate_actions(
        opts.filename,
        pen_up_position=85,
        pen_down_position=35,
    )
    for move in actions:
        print(move)


def test(opts):
    print("Running test action...")
    # bot = EiBotBoard.find()
    try:
        actions = moves.plot_segment_with_velocity((0, 0), (0.01, 0.01), 0, 0, pen_up=True)
        count = len(actions)
        for ii, move in enumerate(actions):
            print("Move %d/%d: %r" % (ii, count, move))
            #bot.do(move)
    finally:
        pass
        #bot.close()


def manual_command(bot, cmd):
    method, *arg = cmd.split()
    arg = tuple(map(int, arg))
    try:
        getattr(bot, method)(*arg)
    except AttributeError as e:
        print("Command not found: %s" % method)
    except (TypeError, ValueError) as e:
        print("Error: %s" % e)


def manual(opts):
    bot = EiBotBoard.find()
    try:
        if opts.cmd:
            cmd = ' '.join(opts.cmd)
            manual_command(bot, cmd)
        else:
            while True:
                cmd = input('(axibot) ')
                manual_command(bot, cmd)
    finally:
        bot.close()


def plot(opts):
    print("Loading %s..." % opts.filename)
    bot = EiBotBoard.find()

    # XXX find pen positions with user interaction?
    pen_up_position = 85
    pen_down_position = 50

    try:
        actions = generate_actions(
            opts.filename,
            pen_up_position=pen_up_position,
            pen_down_position=pen_down_position,
        )
        count = len(actions)
        print("Calculated %d actions." % count)

        bot.pen_up()
        bot.disable_motors()
        print("Pen up and motors off. Move carriage to top left corner.")
        input("Press enter to begin.")

        bot.enable_motors(1)

        for ii, move in enumerate(actions):
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

    p_manual = subparsers.add_parser(
        'manual', help='Manual control shell.')
    p_manual.add_argument('cmd', nargs='*')
    p_manual.set_defaults(function=manual)

    p_test = subparsers.add_parser(
        'test', help='Testing function.')
    p_test.set_defaults(function=test)

    opts, args = p.parse_known_args(args[1:])

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    if opts.function:
        return opts.function(opts)
    else:
        p.print_help()
