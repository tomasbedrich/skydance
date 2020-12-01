import asyncio
import logging
import os
import pytest

from skydance.commands import *
from skydance.controller import Controller
from skydance.session import Session


IP = "192.168.3.218"

log = logging.getLogger(__name__)


@pytest.mark.skipif(
    "CI" in os.environ,
    reason="Manual test is supposed to run against a physical controller "
    "attached to the local network.",
)
@pytest.mark.asyncio
@pytest.mark.parametrize("zone", {1, 2})
async def test_manual_on_blink_temp_off(zone: int):
    async with Session(IP) as sess:
        controller = Controller(sess)

        log.info("Pinging")
        await controller.write(PingCommand())

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
    asyncio.run(test_manual_on_blink_temp_off(zone=2))
