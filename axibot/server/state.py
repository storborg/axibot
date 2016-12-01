"""
Manages the state of the axibot.

Possible system states:

    idle, ready to plot         (idle)
    plotting document           (plotting)
    canceling plotting          (canceling)
    processing document         (processing)

Possible state transitions are:

    idle -> plotting            (begin plotting)
    idle -> processing          (upload)
    processing -> idle          (done)
    plotting -> canceling       (cancel requested)
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
    canceling = 3
    processing = 4
