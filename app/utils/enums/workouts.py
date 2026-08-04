from enum import Enum


class SetType(str, Enum):
    STANDARD = "standard"
    WARMUP = "warmup"
    DROP = "drop"
    FAILURE = "failure"