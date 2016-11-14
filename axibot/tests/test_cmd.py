from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
from axibot.cmd import main

from . import utils


def test_info_smoke():
    filename = os.path.join(utils.example_dir, 'circles.svg')
    args = ['axibot', 'info', filename]
    main(args)
