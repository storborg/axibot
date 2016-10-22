import sys
import argparse


def main(args=sys.argv):
    p = argparse.ArgumentParser(description='Print with the AxiDraw.')
    p.add_argument('--verbose', action='store_true')
    p.add_argument('filename')

    opts = p.parse_args(args[1:])
    print("Loading %s..." % opts.filename)


def server(args=sys.argv):
    p = argparse.ArgumentParser(
        description='Run a server for remote printing with the AxiDraw.')
    p.add_argument('--verbose', action='store_true')
    p.add_argument('--port', type=int, default=8888)

    opts = p.parse_args(args[1:])
    print("Serving on port %d..." % opts.port)
