import enum

class CHANNELS(enum.IntEnum):
    HOLEPUNCH = enum.auto()
    CONTROL = enum.auto()
    STATS = enum.auto()
    VIDEO = enum.auto()
    MAX = enum.auto()


class ERROR(enum.IntEnum):
    ERROR = enum.auto()
    OK = enum.auto()
    MALFORMED_TIME = enum.auto()
    INVALID_TIME = enum.auto()
    INVALID_LENGTH = enum.auto()
    TEMP_MINMAX = enum.auto()
    PH_MINMAX = enum.auto()
    FEED_ERROR = enum.auto()


class MESSAGE(enum.IntEnum):
    GET_SETTINGS = enum.auto()
    GET_STATS = enum.auto()
    MANUAL_FEED = enum.auto()
    SET_FEED_TIME = enum.auto()
    SET_FEED_LENGTH = enum.auto()
    SET_TEMP_WARNING = enum.auto()
    SET_PH_WARNING = enum.auto()
    RESET_SETTINGS = enum.auto()
    SAVE_SETTINGS = enum.auto()
