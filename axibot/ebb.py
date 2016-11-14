from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging

import serial
from serial.tools.list_ports import comports

from . import config

log = logging.getLogger(__name__)


class EiBotException(Exception):
    pass


class EiBotBoard:
    def __init__(self, ser):
        self.serial = ser

    @classmethod
    def list_ports(cls):
        ports = comports()
        for port in ports:
            if port[1].startswith('EiBotBoard'):
                yield port[0]
            elif port[2].startswith('USB VID:PID=04D8:FD92'):
                yield port[0]

    @classmethod
    def open(cls, port):
        ser = serial.Serial(port, timeout=1.0)
        # May need to try several times to get a response from the board?
        # This behavior is taken from the ebb_serial usage, not sure if it's
        # necessary.
        for attempt in range(3):
            ser.write(b'v\r')
            version = ser.readline()
            if version and version.startswith(b'EBB'):
                return cls(ser)

    @classmethod
    def find(cls):
        for port in cls.list_ports():
            if port:
                return cls.open(port)
        raise EiBotException("Could not find a connected EiBotBoard.")

    def close(self):
        # XXX Maybe switch to a context manger for this?
        self.serial.close()

    def robust_readline(self):
        for attempt in range(config.MAX_RETRIES):
            resp = self.serial.readline()
            if resp:
                return resp

    def query(self, cmd):
        self.serial.write(cmd.encode('ascii'))
        resp = self.robust_readline()
        if cmd.strip().lower() not in ('v', 'i', 'a', 'mr', 'pi', 'qm'):
            # Discard response.
            self.robust_readline()
        return resp

    def command(self, cmd):
        cmd = cmd.encode('ascii')
        log.debug("Sending command: %s", cmd)
        self.serial.write(cmd)
        resp = self.robust_readline()
        if not resp.strip().startswith(b'OK'):
            if resp:
                raise EiBotException(
                    "Unexpected response from EBB:\n"
                    "Command: %s\n"
                    "Response: %s" % (cmd.strip(), resp.strip()))

    def timed_pause(self, n):
        while n:
            if n > 750:
                td = int(750)
            else:
                td = n
                if td < 1:
                    td = int(1)
            self.command('SM,%s,0,0\r' % td)
            n -= td

    def enable_motors(self, res):
        """
        Enable motors. Available resolutions:
            0, -> Motor disabled
            1, -> 16X microstepping
            2, -> 8X microstepping
            3, -> 4X microstepping
            4, -> 2X microstepping
            5, -> No microstepping
        """
        if res < 0:
            res = 0
        elif res > 5:
            res = 5
        self.command('EM,%s,%s\r' % (res, res))

    def disable_motors(self):
        self.command('EM,0,0\r')

    def query_prg_button(self):
        self.command('QB\r')

    def toggle_pen(self):
        self.command('TP\r')

    def servo_setup(self,
                    pen_down_position, pen_up_position,
                    servo_up_speed, servo_down_speed):
        """
        Configure EBB servo control offsets and speeds.

        From the axidraw.py comments:

            "Pen position units range from 0% to 100%, which correspond to a
            typical timing range of 7500 - 25000 in units of 1/(12 MHz). 1%
            corresponds to ~14.6 us, or 175 units of 1/(12 MHz)."

            "Servo speed units are in units of %/second, referring to the
            percentages above.  The EBB takes speeds in units of 1/(12 MHz)
            steps per 24 ms.  Scaling as above, 1% of range in 1 second with
            SERVO_MAX = 28000  and  SERVO_MIN = 7500 corresponds to 205 steps
            change in 1 s That gives 0.205 steps/ms, or 4.92 steps / 24 ms
            Rounding this to 5 steps/24 ms is sufficient."
        """
        slope = float(config.SERVO_MAX - config.SERVO_MIN) / 100.
        up_setting = int(round(config.SERVO_MIN + (slope * pen_up_position)))
        down_setting = int(round(config.SERVO_MIN +
                                 (slope * pen_down_position)))
        up_speed = 5 * servo_up_speed
        down_speed = 5 * servo_down_speed
        self.command('SC,4,%s\r' % up_setting)
        self.command('SC,5,%s\r' % down_setting)
        self.command('SC,11,%s\r' % up_speed)
        self.command('SC,12,%s\r' % down_speed)

    def pen_up(self, delay):
        self.command('SP,1,%s\r' % delay)

    def pen_down(self, delay):
        self.command('SP,0,%s\r' % delay)

    def xy_accel_move(self, dx, dy, v_initial, v_final):
        """
        Move X/Y axes as: "AM,<v_initial>,<v_final>,<axis1>,<axis2><CR>"
        Typically, this is wired up such that axis 1 is the Y axis and axis 2
        is the X axis of motion. On EggBot, Axis 1 is the "pen" motor, and Axis
        2 is the "egg" motor. Note that minimum move duration is 5 ms.
        Important: Requires firmware version 2.4 or higher.

        Not used in "stock" AxiDraw Inkscape driver: theoretically this could
        replace a substantial portion of the motion planning, and eliminate the
        plot_segment... planning, but there are some comments in firmware code
        and such that indicate that it doesn't work correctly yet.
        """
        self.command('AM,%s,%s,%s,%s\r' % (v_initial, v_final, dx, dy))

    def xy_move(self, m1, m2, duration):
        """
        Move M1/M2 axes as: "SM,<move_duration>,<axis1>,<axis2><CR>"

        Move duration is in milliseconds and can be 1 to 16777215.
        m1 and m2 are in steps and are signed 24-bit integers.

        On the AxiDraw, these axes are blended: the coordinate space of the
        control API is rotated 45 degrees from the coordinate space of the
        actual movement. It's unclear why this is.
        """
        assert isinstance(m1, int)
        assert isinstance(m2, int)
        assert isinstance(duration, int)
        assert (duration >= 1) and (duration <= 16777215), \
            "Invalid duration %r" % duration

        # XXX add checks for minimum or maximum step rates

        self.command('SM,%s,%s,%s\r' % (duration, m1, m2))

    def ab_move(self, da, db, duration):
        """
        Issue command to move A/B axes
        as: "XM,<move_duration>,<axisA>,<axisB><CR>"
        Then, <Axis1> moves by <AxisA> + <AxisB>,
        and <Axis2> as <AxisA> - <AxisB>

        Not used in "stock" AxiDraw Inkscape driver.
        """
        self.command('XM,%s,%s,%s\r' % (duration, da, db))

    def do(self, move):
        kw = move.__dict__.copy()
        name = move.name
        if name in ('pen_up', 'pen_down',
                    'xy_accel_move', 'xy_move',
                    'ab_move'):
            method = getattr(self, name)
            return method(**kw)
        else:
            raise EiBotException("Don't know how to do move %r / %s" %
                                 (move, move))
