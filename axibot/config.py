from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
MAX_RETRIES = 100

# These are unitless timing values used by the EBB.
SERVO_MIN = 7500
SERVO_MAX = 28000

# Default
SERVO_SPEED = 150

# Milliseconds?
EXTRA_PEN_UP_DELAY = 0
EXTRA_PEN_DOWN_DELAY = 0

SPEED_SCALE = 24.950  # ticks per millisecond

# Milliseconds of acceleration to reach full speed with pen down.
ACCEL_TIME_PEN_DOWN = 250

# Speed in ticks per millisecond.
SPEED_PEN_DOWN = 0.25 * SPEED_SCALE

# Milliseconds of acceleration to reach full speed with pen up.
ACCEL_TIME_PEN_UP = 1000

# Speed in ticks per millisecond.
SPEED_PEN_UP = 0.75 * SPEED_SCALE

# Short-move pen-up distance threshold in inches, below which we use the faster
# pen-down acceleration rate.
SHORT_THRESHOLD = 1.0

# Motor steps per inch in 16X microstepping mode.
DPI_16X = 2032

# Time interval in milliseconds to update motor control.
TIME_SLICE = 30

# Smoothness of curves. Units are inches.
CURVE_RESOLUTION = 0.02

# Skip pen-up moves shorter than this distance when possible. Units in inches.
MIN_GAP = 0.010
