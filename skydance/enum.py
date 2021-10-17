from enum import Enum


class ZoneType(Enum):
    Switch = 0x01
    Dimmer = 0x11
    CCT = 0x21
    RGB = 0x31
    RGBW = 0x41
    RGBCCT = 0x51
