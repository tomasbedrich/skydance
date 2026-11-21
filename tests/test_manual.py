import logging
import os
import pytest
from functools import partial

from skydance.network.discovery import discover_ips_by_mac
from skydance.network.session import Session
from skydance.protocol import *


pytestmark = pytest.mark.skipif(
    "CI" in os.environ,
    reason="Manual test is supposed to run against a physical Wi-Fi relay "
    "attached to the local network.",
)

IP = os.getenv("IP", default="192.168.88.113")
IP_BROADCAST = "192.168.3.255"

log = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.fixture(name="session")
async def session_fixture():
    async with Session(IP, PORT) as session:
        yield session


@pytest.mark.asyncio
async def test_number_of_zones(session):
    raw = await session.request(GetNumberOfZonesCommand)
    log.info("Got number_of_zones=%d", GetNumberOfZonesResponse(raw).number)


@pytest.mark.asyncio
async def test_state_frame_number_overflow(session):
    log.info("Testing State.frame_number overflow")
    for _ in range(256):
        raw = await session.request(GetNumberOfZonesCommand)
        log.debug("Got number_of_zones=%d", GetNumberOfZonesResponse(raw).number)


@pytest.mark.asyncio
async def test_zone_discovery(session):
    log.info("Getting number of zones")
    raw = await session.request(GetNumberOfZonesCommand)

    for zone in GetNumberOfZonesResponse(raw).zones:
        log.info("Getting info about zone=%d", zone)
        raw = await session.request(partial(GetZoneInfoCommand, zone=zone))
        zone_info = GetZoneInfoResponse(raw)
        log.info("Zone=%d has type=%s, name=%s", zone, zone_info.type, zone_info.name)


@pytest.mark.asyncio
async def test_ping(session):
    log.info("Pinging")
    await session.request(PingCommand)


@pytest.mark.asyncio
async def test_master_on_off(session):
    log.info("Master on")
    await session.request(MasterPowerOnCommand)

    log.info("Master off")
    await session.request(MasterPowerOffCommand)


@pytest.mark.asyncio
@pytest.mark.parametrize("zone", {1, 2, 3})
async def test_on_blink_temp_off(session, zone: int):
    log.info("Powering on")
    await session.request(partial(PowerOnCommand, zone=zone))

    log.info("Starting blink sequence")
    await session.request(partial(BrightnessCommand, zone=zone, brightness=1))
    await session.request(partial(BrightnessCommand, zone=zone, brightness=255))

    log.info("Starting white temperature change sequence")
    await session.request(partial(TemperatureCommand, zone=zone, temperature=255))
    await session.request(partial(TemperatureCommand, zone=zone, temperature=0))

    log.info("Starting RGBW change sequence")
    for red, green, blue, white in (
        (255, 0, 0, 0),
        (0, 255, 0, 0),
        (0, 0, 255, 0),
        (0, 0, 0, 255),
    ):
        await session.request(
            partial(
                RGBWCommand, zone=zone, red=red, green=green, blue=blue, white=white
            )
        )

    log.info("Powering off")
    await session.request(partial(PowerOffCommand, zone=zone))


@pytest.mark.asyncio
@pytest.mark.parametrize("ip,broadcast", {(IP, False), (IP_BROADCAST, True)})
async def test_discovery(ip, broadcast):
    res = await discover_ips_by_mac(ip, broadcast=broadcast)
    for mac, ips in res.items():
        log.info("Discovered MAC: %s, IPs: %s", mac.hex(":"), ",".join(map(str, ips)))
