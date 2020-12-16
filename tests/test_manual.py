import asyncio
import logging
import os
import pytest

from skydance.commands import *
from skydance.controller import Controller
from skydance.session import Session


pytestmark = pytest.mark.skipif(
    "CI" in os.environ,
    reason="Manual test is supposed to run against a physical controller "
    "attached to the local network.",
)

IP = "192.168.3.218"

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_zone_discovery():
    async with Session(IP) as sess:
        controller = Controller(sess)

        log.info("Getting number of zones")
        await controller.write(GetNumberOfZonesCommand())
        number_of_zones = GetNumberOfZonesResponse(await controller.read()).number

        for zone in range(1, number_of_zones + 1):
            log.info("Getting name of zone=%d", zone)
            await controller.write(GetZoneNameCommand(zone=zone))
            zone_name = GetZoneNameResponse(await controller.read()).name
            log.info("Zone=%d has name=%s", zone, zone_name)


@pytest.mark.asyncio
async def test_ping():
    async with Session(IP) as sess:
        controller = Controller(sess)

        log.info("Pinging")
        await controller.write(PingCommand())
        await asyncio.sleep(2)


@pytest.mark.asyncio
async def test_master_on_off():
    async with Session(IP) as sess:
        controller = Controller(sess)

        log.info("Master on")
        await controller.write(MasterPowerOnCommand())
        await asyncio.sleep(2)

        log.info("Master off")
        await controller.write(MasterPowerOffCommand())
        await asyncio.sleep(2)


@pytest.mark.asyncio
@pytest.mark.parametrize("zone", {1, 2})
async def test_on_blink_temp_off(zone: int):
    async with Session(IP) as sess:
        controller = Controller(sess)

        log.info("Powering on")
        await controller.write(PowerOnCommand(zone=zone))
        await asyncio.sleep(2)

        log.info("Starting blink sequence")
        await controller.write(BrightnessCommand(zone=zone, brightness=1))
        await asyncio.sleep(0.5)
        await controller.write(BrightnessCommand(zone=zone, brightness=255))
        await asyncio.sleep(2)

        log.info("Starting white temperature change sequence")
        await controller.write(TemperatureCommand(zone=zone, temperature=255))
        await asyncio.sleep(0.5)
        await controller.write(TemperatureCommand(zone=zone, temperature=0))
        await asyncio.sleep(2)

        log.info("Powering off")
        await controller.write(PowerOffCommand(zone=zone))
        # note - zone max+1 means controlling all zones at once


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_zone_discovery())
