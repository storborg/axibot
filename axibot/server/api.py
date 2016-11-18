"""
Communication between web user and the axibot server.

Server to client messages:

    state update
    new document
    error
    completed job

Client to server messages:

    set document
    manual pen up
    manual pen down
    pause plotting
    resume plotting
    cancel plotting
"""
import json


class Message:
    def serialize(self):
        d = self.__dict__.copy()
        d['type'] = self.reverse_types[self.__class__]
        return json.dumps(d)

    @classmethod
    def deserialize(cls, raw):
        msg_class = cls.types[raw.pop('type')]
        return msg_class(**raw)


class StateMessage(Message):
    """
    Inform a connected client that the server's state has changed.
    """
    def __init__(self, state, num_actions, action_index):
        self.state = state
        self.num_actions = num_actions
        self.action_index = action_index


class NewDocumentMessage(Message):
    """
    Inform a connected client that there is a new active document. The client
    should then request it.
    """
    pass


class ErrorMessage(Message):
    """
    Inform a connected client of an error on the server.
    """
    def __init__(self, text):
        self.text = text


class CompletedJobMessage(Message):
    """
    Inform a connected client that the current plotting job has finished, and
    provide stats about it.
    """
    def __init__(self, estimated_time, actual_time):
        self.estimated_time = estimated_time
        self.actual_time = actual_time


class SetDocumentMessage(Message):
    """
    Instruct the server to set a new active document.
    XXX
    """
    pass


class ManualPenUpMessage(Message):
    """
    Instruct the server to lift the pen up.
    """
    pass


class ManualPenDownMessage(Message):
    """
    Instruct the server to drop the pen down.
    """
    pass


class PausePlottingMessage(Message):
    """
    Instruct the server to pause plotting.
    """
    pass


class ResumePlottingMessage(Message):
    """
    Instruct the server to resume plotting.
    """
    pass


class CancelPlottingMessage(Message):
    """
    Instruct the server to cancel plotting the current job.
    """
    pass


Message.types = {
    'state': StateMessage,
    'new-document': NewDocumentMessage,
    'error': ErrorMessage,
    'completed-job': CompletedJobMessage,
    'set-document': SetDocumentMessage,
    'manual-pen-up': ManualPenUpMessage,
    'manual-pen-down': ManualPenDownMessage,
    'pause-plotting': PausePlottingMessage,
    'resume-plotting': ResumePlottingMessage,
    'cancel-plotting': CancelPlottingMessage,
}

Message.reverse_types = {v: k for k, v in Message.types.items()}
