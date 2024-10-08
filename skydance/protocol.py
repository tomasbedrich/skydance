import struct
from abc import ABCMeta, abstractmethod
from functools import partial

from skydance.enum import ZoneType


PORT = 8899
"""A port used for communication with a relay."""

HEAD = bytes.fromhex("55 aa 5a a5 7e")
"""A magic byte sequence used as a header for each command and response."""

TAIL = bytes.fromhex("00 7e")
"""A magic byte sequence marking end of each command and response."""

# This is repeated through many commands, don't know why yet.
# It probably has something to do with a relay ID.
# But as reported by other users, it is working with hardcoded ID as well.
# See: https://github.com/tomasbedrich/home-assistant-skydance/issues/1
_COMMAND_MAGIC = bytes.fromhex("80 00 80 e1 80 00 00")

DEVICE_BASE_TYPE_NORMAL = 0x80


class State:
    """Holds state of a connection."""

    _frame_number: int

    def __init__(self):
        self._frame_number = 0

    def increment_frame_number(self):
        """
        Increment a frame number used by a relay to reconstruct a network stream.

        !!! important
            The frame number must be (manually) incremented after each command.
        """
        self._frame_number = (self._frame_number + 1) % 256

    @property
    def frame_number(self) -> bytes:
        return bytes([self._frame_number])


class Command(metaclass=ABCMeta):
    """A base command."""

    def __init__(self, state: State):
        """
        Create a Command.

        Args:
            state: A state of connection used to generate byte output of a command.
        """
        self.state = state

    @property
    def raw(self):
        """Return complete byte output of a command ready to send over network."""
        return bytes().join((HEAD, self.state.frame_number, self.body, TAIL))

    @property
    @abstractmethod
    def body(self) -> bytes:
        """
        Return byte body which represents the command core.

        The returned value exclude [HEAD][skydance.protocol.HEAD],
        frame number and [TAIL][skydance.protocol.TAIL]. These are added
        automatically in [`Command.raw`][skydance.protocol.Command.raw].
        """


class PingCommand(Command):
    """Ping a relay to raise a communication error if something is wrong."""

    body = bytes.fromhex("80 00 80 e1 80 00 00 01 00 79 00 00")


class ZoneCommand(Command, metaclass=ABCMeta):
    """A base command which controls a specific Zone."""

    def __init__(self, *args, zone: int, **kwargs):
        """
        Create a ZoneCommand.

        Args:
            *args: See [Command][skydance.protocol.Command].
            zone: A zone number to control.
            **kwargs: See [Command][skydance.protocol.Command].
        """
        super().__init__(*args, **kwargs)
        self.validate_zone(zone)
        self.zone = zone

    @staticmethod
    def validate_zone(zone: int):
        """
        Validate a zone number.

        Raise:
            ValueError: If zone number is invalid.
        """
        try:
            if not 0 <= zone <= 255:
                raise ValueError("Zone number must fit into one byte.")
        except TypeError as e:
            raise ValueError("Zone number must be int-like.") from e


class PowerCommand(ZoneCommand):
    """Power a Zone on/off."""

    def __init__(self, *args, power: bool, **kwargs):
        """
        Create a PowerCommand.

        Args:
            *args: See [ZoneCommand][skydance.protocol.ZoneCommand].
            power: A power on/off state.
            **kwargs: See [ZoneCommand][skydance.protocol.ZoneCommand].
        """
        super().__init__(*args, **kwargs)
        self.power = power

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _COMMAND_MAGIC,
                # TODO: zone number is probably a 2 byte bitmask of what zones to power on/off
                struct.pack("<H", 1 << (self.zone - 1)),
                bytes.fromhex("0a 01 00"),
                bytes.fromhex("01" if self.power else "00"),
            )
        )


PowerOnCommand = partial(PowerCommand, power=True)
PowerOffCommand = partial(PowerCommand, power=False)


class MasterPowerCommand(Command):
    """Power all zones on/off."""

    def __init__(self, *args, power: bool, **kwargs):
        """
        Create a MasterPowerCommand.

        Args:
            *args: See [Command][skydance.protocol.Command].
            power: A power on/off state.
            **kwargs: See [Command][skydance.protocol.Command].
        """
        super().__init__(*args, **kwargs)
        self.power = power

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _COMMAND_MAGIC,
                bytes.fromhex("0F FF 0B 03 00"),
                bytes.fromhex("03" if self.power else "00"),
                bytes.fromhex("00"),
                bytes.fromhex("01" if self.power else "00"),
            )
        )


MasterPowerOnCommand = partial(MasterPowerCommand, power=True)
MasterPowerOffCommand = partial(MasterPowerCommand, power=False)


class BrightnessCommand(ZoneCommand):
    """Change brightness of a Zone."""

    def __init__(self, *args, brightness: int, **kwargs):
        """
        Create a BrightnessCommand.

        Args:
            *args: See [ZoneCommand][skydance.protocol.ZoneCommand].
            brightness: A brightness level between 1-255 (higher = more bright).
            **kwargs: See [ZoneCommand][skydance.protocol.ZoneCommand].
        """
        super().__init__(*args, **kwargs)
        self.validate_brightness(brightness)
        self.brightness = brightness

    @staticmethod
    def validate_brightness(brightness: int):
        """
        Validate a brightness level.

        Raise:
            ValueError: If brightness level is invalid.
        """
        try:
            if not 1 <= brightness <= 255:
                raise ValueError("Brightness level must fit into one byte and be >= 1.")
        except TypeError as e:
            raise ValueError("Brightness level must be int-like.") from e

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _COMMAND_MAGIC,
                struct.pack("<H", 2 ** (self.zone - 1)),
                bytes.fromhex("07 02 00 00"),
                struct.pack("B", self.brightness),
            )
        )


class TemperatureCommand(ZoneCommand):
    """Change white temperature of a Zone."""

    def __init__(self, *args, temperature: int, **kwargs):
        """
        Create a TemperatureCommand.

        Args:
            *args: See [ZoneCommand][skydance.protocol.ZoneCommand].
            temperature: A temperature level between 0-255 (higher = more cold).
            **kwargs: See [ZoneCommand][skydance.protocol.ZoneCommand].
        """
        super().__init__(*args, **kwargs)
        self.validate_temperature(temperature)
        self.temperature = temperature

    @staticmethod
    def validate_temperature(temperature: int):
        """
        Validate a temperature level.

        Raise:
            ValueError: If temperature level is invalid.
        """
        try:
            if not 0 <= temperature <= 255:
                raise ValueError("Temperature level must fit into one byte.")
        except TypeError as e:
            raise ValueError("Temperature level must be int-like.") from e

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _COMMAND_MAGIC,
                struct.pack("<H", 2 ** (self.zone - 1)),
                bytes.fromhex("0D 02 00 00"),
                struct.pack("B", self.temperature),
            )
        )


class RGBWCommand(ZoneCommand):
    """Change color of a Zone."""

    def __init__(self, *args, red: int, green: int, blue: int, white: int, **kwargs):
        """
        Create a RGBWCommand.

        All component levels are between 0-255,
        where higher number means more intensive color component.

        At least one color component must be set to non-zero.

        Args:
            *args: See [ZoneCommand][skydance.protocol.ZoneCommand].
            red: A red level.
            green: A green level.
            blue: A blue level.
            white: A white level.
            **kwargs: See [ZoneCommand][skydance.protocol.ZoneCommand].
        """
        super().__init__(*args, **kwargs)

        self.validate_component(red, hint="red")
        self.validate_component(green, hint="green")
        self.validate_component(blue, hint="blue")
        self.validate_component(white, hint="white")

        if not red and not green and not blue and not white:
            raise ValueError("At least one color component must be set to non-zero.")

        self.red = red
        self.green = green
        self.blue = blue
        self.white = white

    @staticmethod
    def validate_component(component: int, hint: str):
        """
        Validate a component level.

        Raise:
            ValueError: If component level is invalid.
        """
        try:
            if not 0 <= component <= 255:
                raise ValueError(f"Component level of {hint} must fit into one byte.")
        except TypeError as e:
            raise ValueError(f"Component level of {hint} must be int-like.") from e

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _COMMAND_MAGIC,
                struct.pack("<H", 2 ** (self.zone - 1)),
                bytes.fromhex("01 07 00"),
                struct.pack("B", self.red),
                struct.pack("B", self.green),
                struct.pack("B", self.blue),
                struct.pack("B", self.white),
                bytes.fromhex("00 00 00"),
            )
        )


class GetNumberOfZonesCommand(Command):
    """Get number of zones available."""

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _COMMAND_MAGIC,
                bytes.fromhex("01 00 79 00 00"),
            )
        )


class GetZoneInfoCommand(ZoneCommand):
    """Discover a zone according to it's number."""

    @property
    def body(self) -> bytes:
        return bytes().join(
            (
                _COMMAND_MAGIC,
                struct.pack("<H", 2 ** (self.zone - 1)),
                bytes.fromhex("78 00 00"),
            )
        )

    @staticmethod
    def validate_zone(zone: int):
        """
        Validate a zone number.

        It may be invalid either because it is not a number
        or it may be outside of range defined by a SkyDance app.

        Raise:
            ValueError: If zone number is invalid.
        """
        try:
            if not 1 <= zone <= 16:
                raise ValueError("Zone number must be between 1 and 16.")
        except TypeError as e:
            raise ValueError("Zone number must be int-like.") from e


class Response(metaclass=ABCMeta):
    """A base response."""

    def __init__(self, raw: bytes):
        """
        Create a Response.

        Args:
            raw: Raw bytes received as a response.
        """
        self.raw = raw

        lbody = self.body
        li = 0

        self.device_type = lbody[li : li + 3]
        li += 3

        self.src_addr = struct.unpack("<H", lbody[li : li + 2])[0]
        li += 2

        self.dst_addr = struct.unpack("<H", lbody[li : li + 2])[0]
        li += 2

        self.zone = struct.unpack("<H", lbody[li : li + 2])[0]
        li += 2

        self.cmd_type = (
            struct.unpack("B", lbody[li : li + 1])[0] - DEVICE_BASE_TYPE_NORMAL
        )
        li += 1

        cmd_data_lenght = struct.unpack("<H", lbody[li : li + 2])[0]
        li += 2

        if cmd_data_lenght > 0:
            self.cmd_data = lbody[li : li + cmd_data_lenght]
            li += cmd_data_lenght

    @property
    def body(self) -> bytes:
        """
        Return byte body which represents the command core.

        The returned value exclude [HEAD][skydance.protocol.HEAD],
        frame number and [TAIL][skydance.protocol.TAIL].
        """
        return self.raw[len(HEAD) + 1 : -len(TAIL)]


class GetNumberOfZonesResponse(Response):
    """
    Parse a response for `GetNumberOfZonesCommand`.

    See: [`GetNumberOfZonesCommand`][skydance.protocol.GetNumberOfZonesCommand].
    """

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

    def __init__(self, raw: bytes):
        super().__init__(raw)
        self._zones = []

        for lbyte in self.cmd_data:
            if (lbyte & DEVICE_BASE_TYPE_NORMAL) == DEVICE_BASE_TYPE_NORMAL:
                zoneId = lbyte & 0x1F
                self._zones.append(zoneId)

    @property
    def number(self) -> int:
        """Return number of zones available."""
        return len(self._zones)

    @property
    def zones(self) -> list:
        """Return list of IDs of zones available."""
        return self._zones


class GetZoneInfoResponse(Response):
    """
    Parse a response for `GetZoneInfoCommand`.

    See: [`GetZoneInfoCommand`][skydance.protocol.GetZoneInfoCommand].
    """

    @property
    def type(self) -> ZoneType:
        """Return a zone type."""
        return ZoneType(self.cmd_data[0])

    @property
    def name(self) -> str:
        """Return a zone name."""
        # Name offset experimentally decoded from response packets.
        return self.cmd_data[2:].decode("utf-8", errors="replace").strip(" \x00")
