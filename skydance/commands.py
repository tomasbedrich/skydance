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
    def bytes(self) -> bytes:
        """
        Return bytes which represents this command.

        The returned value must exclude HEAD, frame number and TAIL.
        These are added automatically in ``Controller``.
        """


class PingCommand(Command):
    """Ping controller to raise a communication error if something is wrong."""

    bytes = bytes.fromhex("80 00 80 e1 80 00 00 01 00 79 00 00")


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
    def bytes(self) -> bytes:
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

    def __init__(self, *, state, **kwargs):
        self.state = state
        super().__init__(**kwargs)

    @property
    def bytes(self) -> bytes:
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
    def bytes(self) -> bytes:
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
    def bytes(self) -> bytes:
        return bytes().join(
            (
                _MAGIC,
                struct.pack("B", self.zone),
                bytes().fromhex("00 0D 02 00 00"),
                struct.pack("B", self.temperature),
            )
        )


# Some partial implementations from old version follows:

# async def load_id(self):
#     """Get controller ID for following communication."""
#     log.debug("Getting controller ID")
#     device_type = "80"
#     res = await self._write(HEAD, self.frame_number, device_type,
#           "00 80 e1 80 00 00 01 00 79 00 00", TAIL)
#     self.id = res[11:13] # really?
#     log.info(f"Got controller ID: {self.id.hex(' ')}")
#     # actual ID according to app is: 98D863A59E5C
#
# async def find_devices(self):
#     log.debug("Finding devices")
#     i, n = 1, 1
#     while True:
#         res = await self._write(HEAD, self.frame_number, "c00c800100", self.id,
#               struct.pack("B", n), "007301", struct.pack(">H", i), TAIL)
#         if res[22:24] == bytes([0, 0]):
#             break
#         device_code = res[22:24] + res[12:14]
#         device_name = res[26:41].decode("ascii")
#         log.info(f"Found device: {device_code.hex(' ')}, name: {device_name}")
#         yield device_code
#         i, n = i + 1, 2 ** i
