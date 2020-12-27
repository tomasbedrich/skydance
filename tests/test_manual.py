import asyncio
import logging
import os
import pytest

from skydance.network.buffer import Buffer
from skydance.network.discovery import discover_ips_by_mac
from skydance.network.session import Session
from skydance.protocol import *


pytestmark = pytest.mark.skipif(
    "CI" in os.environ,
    reason="Manual test is supposed to run against a physical controller "
    "attached to the local network.",
)

IP = "192.168.3.218"
IP_BROADCAST = "192.168.3.255"

log = logging.getLogger(__name__)


@pytest.fixture(name="state")
def state_fixture():
    return State()


@pytest.mark.asyncio
@pytest.fixture(name="session")
async def session_fixture():
    async with Session(IP, PORT) as session:
        yield session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chunk_size", range(1, 41)
)  # GetNumberOfZonesResponse is expected to be 36 bytes long
async def test_buffered_read(state, session, chunk_size):
    buffer = Buffer(TAIL)

    log.info("Testing buffered read with chunk_size=%d", chunk_size)
    cmd = GetNumberOfZonesCommand(state).raw
    await session.write(cmd)
    state.increment_frame_number()

    # this is the code under test
    while not buffer.is_message_ready:
        chunk = await session.read(chunk_size)
        buffer.feed(chunk)
    res = buffer.get_message()

    number_of_zones = GetNumberOfZonesResponse(res).number
    log.info("Got number_of_zones=%d ", number_of_zones)


@pytest.mark.asyncio
async def test_state_frame_number_overflow(state, session):
    log.info("Testing State.frame_number overflow")
    for _ in range(256):
        cmd = GetNumberOfZonesCommand(state).raw
        await session.write(cmd)
        state.increment_frame_number()
        res = await session.read(64)
        number_of_zones = GetNumberOfZonesResponse(res).number
        log.debug("Got number_of_zones=%d", number_of_zones)


@pytest.mark.asyncio
async def test_zone_discovery(state, session):
    log.info("Getting number of zones")
    cmd = GetNumberOfZonesCommand(state).raw
    await session.write(cmd)
    state.increment_frame_number()
    res = await session.read(64)
    number_of_zones = GetNumberOfZonesResponse(res).number

    for zone in range(1, number_of_zones + 1):
        log.info("Getting name of zone=%d", zone)
        cmd = GetZoneNameCommand(state, zone=zone).raw
        await session.write(cmd)
        state.increment_frame_number()
        res = await session.read(64)
        zone_name = GetZoneNameResponse(res).name
        log.info("Zone=%d has name=%s", zone, zone_name)


@pytest.mark.asyncio
async def test_ping(state, session):
    log.info("Pinging")
    cmd = PingCommand(state).raw
    await session.write(cmd)


@pytest.mark.asyncio
async def test_master_on_off(state, session):
    log.info("Master on")
    cmd = MasterPowerOnCommand(state).raw
    await session.write(cmd)
    state.increment_frame_number()
    await asyncio.sleep(2)

    log.info("Master off")
    cmd = MasterPowerOffCommand(state).raw
    await session.write(cmd)
    state.increment_frame_number()
    await asyncio.sleep(2)


@pytest.mark.asyncio
@pytest.mark.parametrize("zone", {1, 2})
async def test_on_blink_temp_off(state, session, zone: int):
    log.info("Powering on")
    cmd = PowerOnCommand(state, zone=zone).raw
    await session.write(cmd)
    state.increment_frame_number()
    await asyncio.sleep(2)

    log.info("Starting blink sequence")
    cmd = BrightnessCommand(state, zone=zone, brightness=1).raw
    await session.write(cmd)
    state.increment_frame_number()
    await asyncio.sleep(0.5)
    cmd = BrightnessCommand(state, zone=zone, brightness=255).raw
    await session.write(cmd)
    state.increment_frame_number()
    await asyncio.sleep(2)

    log.info("Starting white temperature change sequence")
    cmd = TemperatureCommand(state, zone=zone, temperature=255).raw
    await session.write(cmd)
    state.increment_frame_number()
    await asyncio.sleep(0.5)
    cmd = TemperatureCommand(state, zone=zone, temperature=0).raw
    await session.write(cmd)
    state.increment_frame_number()
    await asyncio.sleep(2)

    log.info("Powering off")
    cmd = PowerOffCommand(state, zone=zone).raw
    await session.write(cmd)
    state.increment_frame_number()
    # note - zone max+1 means controlling all zones at once


@pytest.mark.asyncio
@pytest.mark.parametrize("ip,broadcast", {(IP, False), (IP_BROADCAST, True)})
async def test_discovery(ip, broadcast):
    res = await discover_ips_by_mac(ip, broadcast=broadcast)
    for mac, ips in res.items():
        log.info("Discovered MAC: %s, IPs: %s", mac.hex(":"), ",".join(map(str, ips)))
