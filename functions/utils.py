import enum


class Types(enum.Enum):
    ACCOUNTS = 'accounts'
    INPUTS = 'dynamic-inputs'
    TEXTAREA = 'dynamic-text-area'
    SETTINGS = 'settings'
    POLL = 'poll-input'
    REACTIONS = 'reaction-input'


class Field:
    def __init__(self, type_: Types, label_name='Label name', **kwargs):
        self.type_ = type_
        self.data = {'label_name': label_name, **kwargs}
