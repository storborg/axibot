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

    plotting -> idle-doc        (completed plotting)
    plotting -> paused          (paused)

    paused -> plotting          (resumed plotting)
    paused -> idle-doc          (cancelled plotting)

Additional state variables are:

    active document (SVG)
    list of actions (or maybe this should just be the number of actions??)
    current action index
"""
