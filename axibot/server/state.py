"""
Manages the state of the axibot.

Possible system states:

    idle, ready to plot         (idle)
    plotting document           (plotting)
    pausing plotting            (pausing)
    paused plotting             (paused)
    canceling plotting          (canceling)

Possible state transitions are:

    idle -> plotting            (begin plotting)

    plotting -> pausing         (pause)
    plotting -> canceling       (cancel)

    pausing -> paused           (paused)

    paused -> idle              (canceled)
    paused -> plotting          (resume)

    canceling -> idle           (canceled)

Additional state variables are:

    active document (SVG text)
    list of actions grouped by path
    current path index
    current progress?

The app also holds a reference to the active EiBotBoard instance.
"""
from enum import Enum


class State(Enum):
    idle = 1
    plotting = 2
    pausing = 3
    paused = 4
    canceling = 5
