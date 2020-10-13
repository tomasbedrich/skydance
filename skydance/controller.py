# see:
# http://dokuwiki.espaiweb.net
# https://community.home-assistant.io/t/skydance-2-4g-rf/99399

# pylint: disable=line-too-long

import asyncio
import logging
import struct
from typing import Union


log = logging.getLogger(__name__)

DEFAULT_PORT = 8899
HEAD = bytes.fromhex("55aa5aa57e")
TAIL = bytes.fromhex("007e")


class Controller:
    # id: bytes

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # the attributes are public mainly for testing purposes
        self.reader, self.writer = reader, writer
        self._reset_frame_number()

    def _increment_frame_number(self):
        self.frame_number[0] = (self.frame_number[0] + 1) % 256

    def _reset_frame_number(self):
        self.frame_number = bytearray.fromhex("00")

    async def _write(self, *data: Union[str, bytes]):
        # allow passing arbitrary splitted data
        req = bytes()
        for part in data:
            if isinstance(part, str):
                req += bytes.fromhex(part)
            else:
                req += part

        # TODO: retry mechanism
        log.debug("Sending: %s", req.hex(' '))
        self.writer.write(req)
        self._increment_frame_number()
        await self.writer.drain()

    async def _read(self):
        res = await self.reader.readuntil(TAIL)
        log.debug("Received: %s", res.hex(' '))
        return res

    async def ping(self):
        """Ping controller to raise a communication error if something is wrong."""
        await self._write(HEAD, self.frame_number, "80 00 80 e1 80 00 00 01 00 79 00 00", TAIL)

    # async def load_id(self):
    #     """Get controller ID for following communication."""
    #     log.debug("Getting controller ID")
    #     device_type = "80"
    #     res = await self._write(HEAD, self.frame_number, device_type, "00 80 e1 80 00 00 01 00 79 00 00", TAIL)
    #     self.id = res[11:13] # really?
    #     log.info(f"Got controller ID: {self.id.hex(' ')}")
    #     # actual ID according to app is: 98D863A59E5C

    # async def find_devices(self):
    #     log.debug("Finding devices")
    #     i, n = 1, 1
    #     while True:
    #         res = await self._write(HEAD, self.frame_number, "c00c800100", self.id, struct.pack("B", n), "007301", struct.pack(">H", i), TAIL)
    #         if res[22:24] == bytes([0, 0]):
    #             break
    #         device_code = res[22:24] + res[12:14]
    #         device_name = res[26:41].decode("ascii")
    #         log.info(f"Found device: {device_code.hex(' ')}, name: {device_name}")
    #         yield device_code
    #         i, n = i + 1, 2 ** i

    # async def master_on(self):
    #     # FIXME
    #     log.debug("Setting master ON")
    #     res = await self._write(HEAD, self.frame_number, self.id, "0F FF 0B", "03 00 00 00", "01", TAIL)
    #     print(res)

    async def power_zone(self, zone: int, state: bool):
        """Turn zone ON/OFF according to state truth value."""
        self.validate_zone(zone)
        log.debug("Setting zone %d %s", zone, 'ON' if state else 'OFF')
        await self._write(
            HEAD,
            self.frame_number,
            "80 00  80 e1 80 00 00",
            struct.pack("B", zone),
            "00 0a 01 00",
            "01" if state else "00",
            TAIL,
        )

    async def dim_zone(self, zone: int, level: int):
        """
        Change brightness of a zone to given level.

        Higher level = more bright.
        """
        self.validate_zone(zone)
        self.validate_dimming_level(level)
        log.debug("Dimming zone %d to %d", zone, level)
        await self._write(
            HEAD,
            self.frame_number,
            "80 00  80 e1 80 00 00",
            struct.pack("B", zone),
            "00 07 02 00 00",
            struct.pack("B", level),
            TAIL,
        )

    async def temp_zone(self, zone: int, temperature: int):
        """
        Change white temperature of a zone to given temperature.

        Higher temperature = more cold.
        """
        self.validate_zone(zone)
        self.validate_white_temperature(temperature)
        log.debug("Setting white color in zone %d to %d", zone, temperature)
        await self._write(
            HEAD,
            self.frame_number,
            "80 00  80 e1 80 00 00",
            struct.pack("B", zone),
            "00 0D 02 00 00",
            struct.pack("B", temperature),
            TAIL,
        )

    @staticmethod
    def validate_zone(zone: int):
        """Raise ValueError if zone number is invalid."""
        try:
            if not 0 <= zone <= 255:
                raise ValueError("Zone number must fit into one byte.")
        except TypeError as e:
            raise ValueError("Zone number must be int-like.") from e

    @staticmethod
    def validate_dimming_level(level: int):
        """Raise ValueError if dimming level is invalid."""
        try:
            if not 1 <= level <= 255:
                raise ValueError("Dimming level must fit into one byte and be <= 1.")
        except TypeError as e:
            raise ValueError("Dimming level must be int-like.") from e

    @staticmethod
    def validate_white_temperature(temp: int):
        """Raise ValueError if white temperature is invalid."""
        try:
            if not 0 <= temp <= 255:
                raise ValueError("White temperature must fit into one byte.")
        except TypeError as e:
            raise ValueError("White temperature must be int-like.") from e
