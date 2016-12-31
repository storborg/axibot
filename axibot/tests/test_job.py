from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ..job import Job
from ..action import XYMove, PenUpMove, PenDownMove


def test_roundtrip():
    job = Job(pen_up_position=60, pen_down_position=40, servo_speed=150)
    job.append(PenDownMove(400))
    job.append(XYMove(500, 300, 200))
    job.append(PenUpMove(400))

    testfile = '/tmp/test.axibot.json'

    with open(testfile, 'w') as f:
        job.serialize(f)

    with open(testfile, 'r') as f:
        newjob = Job.deserialize(f)

    assert job == newjob
