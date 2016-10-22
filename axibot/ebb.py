import serial
from serial.tools.list_ports import comports

from . import moves

MAX_RETRIES = 100


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
            ser.write('v\r')
            version = ser.readline()
            if version and version.startswith('EBB'):
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
        for attempt in range(MAX_RETRIES):
            resp = self.serial.readline()
            if resp:
                return resp

    def query(self, cmd):
        self.serial.write(cmd)
        resp = self.robust_readline()
        if cmd.strip().lower() not in ('v', 'i', 'a', 'mr', 'pi', 'qm'):
            # Discard response.
            self.robust_readline()
        return resp

    def command(self, cmd):
        self.serial.write(cmd)
        resp = self.robust_readline()
        if not resp.strip().startswith('OK'):
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
        """
        self.command('AM,%s,%s,%s,%s\r' % (v_initial, v_final, dx, dy))

    def xy_move(self, dx, dy, duration):
        """
        Move X/Y axes as: "SM,<move_duration>,<axis1>,<axis2><CR>"
        Typically, this is wired up such that axis 1 is the Y axis and axis 2
        is the X axis of motion. On EggBot, Axis 1 is the "pen" motor, and Axis
        2 is the "egg" motor.
        """
        self.command('SM,%s,%s,%s\r' % (duration, dy, dx))

    def ab_move(self, da, db, duration):
        """
        Issue command to move A/B axes as:
            "XM,<move_duration>,<axisA>,<axisB><CR>"
        Then, <Axis1> moves by <AxisA> + <AxisB>,
        and <Axis2> as <AxisA> - <AxisB>
        """
        self.command('MX,%s,%s,%s\r' % (duration, da, db))

    def do(self, move):
        if isinstance(move, moves.PenUpMove):
            self.pen_up()
        elif isinstance(move, moves.PenDownMove):
            self.pen_down()
        elif isinstance(move, moves.XYMove):
            self.xy_move(move.dx, move.dy, move.duration)
        elif isinstance(move, moves.XYAccelMove):
            self.xy_accel_move(move.dx, move.dy, move.v_initial, move.v_final)
        elif isinstance(move, moves.ABMove):
            self.ab_move(move.da, move.db, move.duration)
        else:
            raise EiBotException("Don't know how to do move %r / %s" %
                                 (move, move))
