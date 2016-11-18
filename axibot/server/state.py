"""
Manages the state of the axibot.

Possible system states:

    idle, no active document    (idle-empty)
    processing document         (processing)
    idle, active document       (idle-doc)
    plotting document           (plotting)
    paused plotting             (paused)

Possible state transitions are:

    idle-empty -> processing    (initial upload)

    processing -> idle-doc      (completed processing)
    processing -> idle-empty    (failed to process)

    idle-doc -> plotting        (begin plotting)
    idle-doc -> processing      (new upload)

    plotting -> idle-doc        (completed plotting or cancelled plotting)
    plotting -> paused          (paused)

    paused -> plotting          (resumed plotting)
    paused -> idle-doc          (cancelled plotting)

Additional state variables are:

    active document (SVG text)
    list of actions
    current action index

The app also holds a reference to the active EiBotBoard instance.
"""
from enum import Enum


class State(Enum):
    processing = 1
    idle = 2
    plotting = 3
    paused = 4
