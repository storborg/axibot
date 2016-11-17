"""
Communication between web user and the axibot server.

Server to client messages:

    state update
    new active document
    error
    completed job

Client to server messages:

    new document
    manual pen up
    manual pen down
    pause plotting
    resume plotting
    cancel plotting
"""
import json


class Message:
    def serialize(self):
        return json.dumps(self.__dict__)


class StateMessage(Message):
    def __init__(self, state):
        self.state = state
