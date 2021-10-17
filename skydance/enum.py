from enum import Enum


class ZoneType(Enum):
    """Zone types which are set manually using Skydance official application."""

    Switch = 0x01
    """Can only be switched on-off."""

    Dimmer = 0x11
    """Its brightness can be adjusted."""

    CCT = 0x21
    """Its brightness and temperature can be adjusted."""

    RGB = 0x31
    """Its brightness and RGB color values can be adjusted."""

    RGBW = 0x41
    """Its brightness and RGBW color values can be adjusted."""

    RGBCCT = 0x51
    """Its brightness, RGBW color values and temperature can be adjusted."""
