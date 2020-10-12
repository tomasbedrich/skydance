import asyncio
import logging
import os
import pytest

from skydance.controller import DEFAULT_PORT, Controller


IP = "192.168.3.218"


@pytest.mark.skipif(
    "CI" in os.environ,
    reason="Manual test is supposed to run against a physical controller "
    "attached to the local network.",
)
@pytest.mark.asyncio
@pytest.mark.parametrize("zone", {1, 2})
async def test_manual_on_blink_temp_off(zone: int):
    print("Opening connection")
    reader, writer = await asyncio.open_connection(IP, DEFAULT_PORT)
    controller = Controller(reader, writer)

    print("Powering on")
    await controller.power_zone(zone, True)
    await asyncio.sleep(2)

    print("Starting blink sequence")
    await controller.dim_zone(zone, 1)
    await asyncio.sleep(0.5)
    await controller.dim_zone(zone, 255)
    await asyncio.sleep(2)

    print("Starting color temperature change sequence")
    await controller.temp_zone(zone, 255)
    await asyncio.sleep(0.5)
    await controller.temp_zone(zone, 0)
    await asyncio.sleep(2)

    print("Powering off")
    await controller.power_zone(zone, False)
    # note - zone max+1 means controlling all zones at once

    print("Closing connection")
    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_manual_on_blink_temp_off(zone=2))
