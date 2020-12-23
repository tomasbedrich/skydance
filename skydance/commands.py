import struct
from abc import ABCMeta, abstractmethod
from functools import partial


# This is repeated through many commands, don't know why yet.
# It probably has something to do with a Controller ID.
# But as reported by other users, it is working with hardcoded ID as well.
# See: https://github.com/tomasbedrich/home-assistant-skydance/issues/1
_MAGIC = bytes.fromhex("80 00 80 e1 80 00 00")


class Command(metaclass=ABCMeta):
    """A base command."""

    @property
    @abstractmethod
    def body(self) -> bytes:
        """
        Return bytes which represents this command.

        The returned value must exclude HEAD, frame number and TAIL.
        These are added automatically in ``Controller``.
        """


class PingCommand(Command):
    """Ping controller to raise a communication error if something is wrong."""

    body = bytes.fromhex("80 00 80 e1 80 00 00 01 00 79 00 00")


class ZoneCommand(Command, metaclass=ABCMeta):
    """A command which controls a specific Zone."""

    zone: int
    """A zone number to control."""

    def __init__(self, *, zone):
        self.validate_zone(zone)
        self.zone = zone

    @staticmethod
    def validate_zone(zone: int):
        """Raise ValueError if zone number is invalid."""
        try:
            if not 0 <= zone <= 255:
                raise ValueError("Zone number must fit into one byte.")
        except TypeError as e:
            raise ValueError("Zone number must be int-like.") from e


class PowerCommand(ZoneCommand):
    """Power a Zone on/off."""

    state: bool
    """A power on/off state."""

    def __init__(self, *, state, **kwargs):
        self.state = state
        super().__init__(**kwargs)

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _MAGIC,
                struct.pack("B", self.zone),
                bytes().fromhex("00 0a 01 00"),
                bytes().fromhex("01" if self.state else "00"),
            )
        )


PowerOnCommand = partial(PowerCommand, state=True)
PowerOffCommand = partial(PowerCommand, state=False)


class MasterPowerCommand(Command):
    """Power all zones on/off."""

    state: bool
    """A power on/off state."""

    def __init__(self, *, state):
        self.state = state

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _MAGIC,
                bytes().fromhex("0F FF 0B 03 00"),
                bytes().fromhex("03" if self.state else "00"),
                bytes().fromhex("00"),
                bytes().fromhex("01" if self.state else "00"),
            )
        )


MasterPowerOnCommand = partial(MasterPowerCommand, state=True)
MasterPowerOffCommand = partial(MasterPowerCommand, state=False)


class BrightnessCommand(ZoneCommand):
    """Change brightness of a Zone."""

    brightness: int
    """A brightness level between 1-255 (higher = more bright)."""

    def __init__(self, *, brightness, **kwargs):
        self.validate_brightness(brightness)
        self.brightness = brightness
        super().__init__(**kwargs)

    @staticmethod
    def validate_brightness(brightness: int):
        """Raise ValueError if brightness level is invalid."""
        try:
            if not 1 <= brightness <= 255:
                raise ValueError("Brightness level must fit into one byte and be >= 1.")
        except TypeError as e:
            raise ValueError("Brightness level must be int-like.") from e

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _MAGIC,
                struct.pack("B", self.zone),
                bytes().fromhex("00 07 02 00 00"),
                struct.pack("B", self.brightness),
            )
        )


class TemperatureCommand(ZoneCommand):
    """Change white temperature of a Zone."""

    temperature: int
    """A temperature level between 0-255 (higher = more cold)."""

    def __init__(self, *, temperature, **kwargs):
        self.validate_temperature(temperature)
        self.temperature = temperature
        super().__init__(**kwargs)

    @staticmethod
    def validate_temperature(temperature: int):
        """Raise ValueError if temperature level is invalid."""
        try:
            if not 0 <= temperature <= 255:
                raise ValueError("Temperature level must fit into one byte.")
        except TypeError as e:
            raise ValueError("Temperature level must be int-like.") from e

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _MAGIC,
                struct.pack("B", self.zone),
                bytes().fromhex("00 0D 02 00 00"),
                struct.pack("B", self.temperature),
            )
        )


class GetNumberOfZonesCommand(Command):
    """Get number of zones available."""

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _MAGIC,
                bytes().fromhex("01 00 79 00 00"),
            )
        )


class GetZoneNameCommand(ZoneCommand):
    """Discover a zone according to it's number."""

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _MAGIC,
                struct.pack("<H", 2 ** (self.zone - 1)),
                bytes().fromhex("78 00 00"),
            )
        )

    @staticmethod
    def validate_zone(zone: int):
        """
        Raise ValueError if zone number is invalid.

        It may be invalid either because it is not a number
        or it may be outside of range defined by a SkyDance app.
        """
        try:
            if not 1 <= zone <= 16:
                raise ValueError("Zone number must be between 1 and 16.")
        except TypeError as e:
            raise ValueError("Zone number must be int-like.") from e


class Response(metaclass=ABCMeta):
    """A base response."""

    raw: bytes
    """
    Raw bytes received as a response.

    It must exclude HEAD, frame number and TAIL.
    These are removed automatically in ``Controller``.
    """

    def __init__(self, raw: bytes):
        self.raw = raw


class GetNumberOfZonesResponse(Response):
    """Parse a response for ``GetNumberOfZonesCommand``."""

    # The packets looks like:
    # ... omitted ... 83 84 85 86 87 88 89 8a 8b 8c 8d 8e 8f 90 00 7e - 16 zones
    # ... omitted ... 83 84 85 86 87 88 89 8a 8b 8c 8d 8e 8f 00 00 7e - 15 zones
    # ... omitted ... 83 84 85 86 87 88 89 8a 8b 8c 8d 8e 00 00 00 7e - 14 zones
    # ... omitted ... 83 84 85 86 87 88 89 8a 8b 8c 8d 00 00 00 00 7e - 13 zones

    # We can see a clear pattern at the end.
    # It is experimentally proven that the pattern doesn't depend on:
    # - Zone type (dimmer, CCT, RGB, ...)
    # - Zone name
    # - Zone status (on/off)

    @property
    def number(self):
        return sum(1 for zone in self.raw[12:28] if zone != 0)


class GetZoneNameResponse(Response):
    """Parse a response for ``DiscoverZoneCommand``."""

    # Name offset experimentally decoded from response packets.

    @property
    def name(self) -> str:
        return self.raw[14:].decode("ascii", errors="replace").strip(" \x00")
