from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pprint import pformat


class Move:
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, pformat(self.__dict__))

    def __str__(self):
        attrs = ['%s:%s' % (k, v) for k, v in self.__dict__.items()]
        return '%s %s' % (self.name, ' '.join(attrs))


class PenUpMove(Move):
    name = 'pen_up'

    def __init__(self, delay):
        self.delay = delay

    def time(self):
        return self.delay


class PenDownMove(Move):
    name = 'pen_down'

    def __init__(self, delay):
        self.delay = delay

    def time(self):
        return self.delay


class XYMove(Move):
    name = 'xy_move'

    def __init__(self, m1, m2, duration):
        assert isinstance(m1, int), "got %r, wanted an int" % m1
        assert isinstance(m2, int), "got %r, wanted an int" % m2
        assert isinstance(duration, int), "got %r, wanted an int" % duration
        assert (m1 != 0) or (m2 != 0), \
            "m1:%r, m2:%r, one must be nonzero" % (m1, m2)
        assert duration > 0, \
            "duration: %r must be greater than zero" % duration
        assert duration >= 30, \
            "duration: %r must be >= 30ms" % duration
        self.m1 = m1
        self.m2 = m2
        self.duration = duration

    def time(self):
        return self.duration


class XYAccelMove(Move):
    name = 'xy_accel_move'

    # XXX These might be better as "m1" and "m2" rather than dx/dy.
    def __init__(self, dx, dy, v_initial, v_final):
        self.dx = dx
        self.dy = dy
        self.v_initial = v_initial
        self.v_final = v_final

    def time(self):
        raise NotImplementedError


class ABMove(Move):
    name = 'ab_move'

    def __init__(self, da, db, duration):
        self.da = da
        self.db = db
        self.duration = duration

    def time(self):
        raise NotImplementedError
