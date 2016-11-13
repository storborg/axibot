import pytest

from .. import planning, config


vmax = config.SPEED_PEN_DOWN
accel_max = vmax / config.ACCEL_TIME_PEN_DOWN
timeslice = config.TIME_SLICE


def find_peak_velocity(dtarray):
    vpeak = xlast = 0
    for x, duration in dtarray:
        xdiff = x - xlast
        v = xdiff / duration
        if v > vpeak:
            vpeak = v
        xlast = x

    # Fudge factor for float error
    vpeak -= 0.00001

    return vpeak


def test_trapezoidal_from_rest():
    dist = 9000
    dtarray = planning.interpolate_distance(dist, 0, 0,
                                            vmax, accel_max, timeslice)
    total_dist = dtarray[-1][0]
    assert dist == total_dist
    assert find_peak_velocity(dtarray) <= vmax


def test_triangular_from_rest():
    dist = 3780
    dtarray = planning.interpolate_distance(dist, 0, 0,
                                            vmax, accel_max, timeslice)
    total_dist = dtarray[-1][0]
    assert dist == total_dist
    assert find_peak_velocity(dtarray) <= vmax


def test_linear_changing_velocity():
    dist = 150
    dtarray = planning.interpolate_distance(dist, 0.7, 0.75,
                                            vmax, accel_max, timeslice)
    total_dist = dtarray[-1][0]
    assert dist == total_dist
    assert find_peak_velocity(dtarray) <= vmax
