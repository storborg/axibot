from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
from axibot.debug import main

from . import utils


def test_debug_smoke():
    infile = os.path.join(utils.example_dir, 'rectangles.svg')
    outfile = '/tmp/axibot-test-debug.png'
    args = ['axibot-debug',
            'actions',
            '--out',
            outfile,
            infile]
    main(args)
    assert os.path.exists(outfile)
