from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging

import time
import sys
import argparse
import os.path
from datetime import timedelta

from six.moves import input

try:
    import coloredlogs
except ImportError:
    coloredlogs = None

from . import planning, config
from .ebb import EiBotBoard, MockEiBotBoard
from .job import Job

log = logging.getLogger(__name__)


def manual_command(bot, cmd):
    args = cmd.split()
    method = args[0]
    arg = args[1:]
    arg = tuple(map(int, arg))
    try:
        getattr(bot, method)(*arg)
    except AttributeError as e:
        log.error("Command not found: %s", method)
    except (TypeError, ValueError) as e:
        log.error("Error: %s", e)


def manual(opts):
    if opts.mock:
        bot = MockEiBotBoard()
    else:
        bot = EiBotBoard.find()
    try:
        bot.servo_setup(config.PEN_DOWN_POSITION, config.PEN_UP_POSITION,
                        config.SERVO_SPEED, config.SERVO_SPEED)
        if opts.cmd:
            cmd = ' '.join(opts.cmd)
            manual_command(bot, cmd)
        else:
            while True:
                cmd = input('(axibot) ')
                manual_command(bot, cmd)
    finally:
        bot.close()


def human_friendly_timedelta(td):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    pieces = []
    if days:
        pieces.append(("%d days" % days) if days > 1 else "1 day")
    if hours:
        pieces.append(("%d hours" % hours) if hours > 1 else "1 hour")
    if minutes:
        pieces.append(("%d minutes" % minutes) if minutes > 1 else "1 minute")
    if seconds:
        pieces.append(("%d seconds" % seconds) if seconds > 1 else "1 second")
    return ", ".join(pieces)


def load_job(filename):
    if filename.endswith('.svg'):
        with open(filename) as f:
            return planning.plan_job(f.read(), filename)
    elif filename.endswith('.axibot.json'):
        with open(filename) as f:
            return Job.deserialize(f)
    else:
        print("Only .svg and .axibot.json files are supported!")
        raise SystemExit


def plan(opts):
    outfile = opts.out
    if not outfile:
        outfile = opts.filename.rsplit('.', 1)[0] + '.axibot.json'
    if os.path.exists(outfile) and not opts.overwrite:
        print("File '%s' exists, pass --overwrite or --out." % outfile)
    else:
        job = load_job(opts.filename)
        with open(outfile, 'w') as f:
            job.serialize(f)


def info(opts):
    job = load_job(opts.filename)
    td = job.duration()
    log.info("Number of moves: %s", len(job))
    log.info("Expected time: %s", human_friendly_timedelta(td))


def plot(opts):
    job = load_job(opts.filename)
    count = len(job)
    log.info("Loaded %d actions.", count)

    pen_up_delay, pen_down_delay = \
        planning.calculate_pen_delays(job.pen_up_position,
                                      job.pen_down_position,
                                      job.servo_speed)

    if opts.mock:
        bot = MockEiBotBoard()
    else:
        bot = EiBotBoard.find()
    try:
        # The initial pen up might need a fairly slow delay, because we don't
        # know where the servo was before.
        bot.pen_up(pen_up_delay)
        log.info("Configuring servos.")
        bot.disable_motors()
        bot.servo_setup(config.PEN_DOWN_POSITION, config.PEN_UP_POSITION,
                        config.SERVO_SPEED, config.SERVO_SPEED)
        log.info("Pen up and motors off. Move carriage to top left corner.")
        input("Press enter to begin.")

        start_time = time.time()
        bot.enable_motors(1)

        for ii, move in enumerate(job):
            log.info("Move %d/%d: %s" % (ii, count, move))
            bot.do(move)

        bot.pen_up(pen_up_delay)
        end_time = time.time()
        estimated_td = job.duration()
        actual_td = timedelta(seconds=(end_time - start_time))
        print("Finished!")
        print("Expected time: %s" % human_friendly_timedelta(estimated_td))
        print("Actual time: %s" % human_friendly_timedelta(actual_td))
        if opts.mock:
            print("---")
            print("Mock EiBotBoard recorded:")
            print("Max speed: %0.3f steps/ms" % bot.max_speed)
            print("Max acceleration: %0.3f steps/ms delta" %
                  bot.max_acceleration)
    finally:
        bot.close()


def server(opts):
    from axibot.server import serve
    serve(opts)


def main(args=sys.argv):
    p = argparse.ArgumentParser(description='Print with the AxiDraw.')
    p.add_argument('--verbose', action='store_true')
    p.add_argument('--mock', action='store_true')
    p.set_defaults(function=None)

    subparsers = p.add_subparsers(help='sub-command help')

    p_plan = subparsers.add_parser(
        'plan', help='Plan the plotting actions for an SVG file.')
    p_plan.add_argument('filename')
    p_plan.add_argument('--out')
    p_plan.add_argument('--overwrite', action='store_true')
    p_plan.set_defaults(function=plan)

    p_plot = subparsers.add_parser(
        'plot', help='Plot an SVG file directly.')
    p_plot.add_argument('filename')
    p_plot.set_defaults(function=plot)

    p_info = subparsers.add_parser(
        'info', help='Print information about an SVG file.')
    p_info.add_argument('filename')
    p_info.set_defaults(function=info)

    p_server = subparsers.add_parser(
        'server', help='Run a server for remote plotting.')
    p_server.add_argument('--port', type=int, default=8888)
    p_server.set_defaults(function=server)

    p_manual = subparsers.add_parser(
        'manual', help='Manual control shell.')
    p_manual.add_argument('cmd', nargs='*')
    p_manual.set_defaults(function=manual)

    opts, args = p.parse_known_args(args[1:])

    if coloredlogs:
        coloredlogs.install(level='DEBUG' if opts.verbose else 'INFO')
    else:
        logging.basicConfig(level=logging.DEBUG if opts.verbose else
                            logging.INFO)

    if opts.function:
        return opts.function(opts)
    else:
        p.print_help()
