from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import timedelta
import json

from .action import PenUpMove, PenDownMove, XYMove, XYAccelMove, ABMove


class Job(list):
    def __init__(self, *args, pen_up_position, pen_down_position, servo_speed,
                 document=None, filename=None):
        self.filename = filename
        self.document = document
        self.pen_up_position = pen_up_position
        self.pen_down_position = pen_down_position
        self.servo_speed = servo_speed
        list.__init__(self, *args)

    def duration(self):
        duration_ms = sum(action.time() for action in self)
        return timedelta(seconds=(duration_ms / 1000))

    def serialize(self, f):
        actions = []
        for action in self:
            d = action.__dict__
            d['name'] = action.name
            actions.append(d)
        obj = {
            'filename': self.filename,
            'document': self.document,
            'pen_up_position': self.pen_up_position,
            'pen_down_position': self.pen_down_position,
            'servo_speed': self.servo_speed,
            'actions': actions,
        }
        json.dump(obj, f, indent=2)

    @classmethod
    def deserialize(cls, f):
        classes = (PenUpMove, PenDownMove, XYMove, XYAccelMove, ABMove)
        registry = {action_class.name: action_class
                    for action_class in classes}
        obj = json.load(f)
        actions = []
        for action_dict in obj.pop('actions'):
            name = action_dict.pop('name')
            action_class = registry[name]
            action = action_class(**action_dict)
            action.name = name
            actions.append(action)
        return cls(actions, **obj)
