from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import timedelta


class Job(list):
    def __init__(self, *args, filename=None):
        self.filename = filename
        list.__init__(self, *args)

    def duration(self):
        duration_ms = sum(action.time() for action in self)
        return timedelta(seconds=(duration_ms / 1000))
