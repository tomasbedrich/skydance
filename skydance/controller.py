# see:
# http://dokuwiki.espaiweb.net
# https://community.home-assistant.io/t/skydance-2-4g-rf/99399

from skydance.commands import Command
from skydance.constants import HEAD, TAIL
from skydance.session import Session


class Controller:
    def __init__(self, session: Session):
        self.session = session
        self._reset_frame_number()

    def _increment_frame_number(self):
        self.frame_number[0] = (self.frame_number[0] + 1) % 256

    def _reset_frame_number(self):
        self.frame_number = bytearray.fromhex("00")

    async def write(self, command: Command):
        req = bytes().join((HEAD, self.frame_number, command.bytes, TAIL))

        # TODO retry mechanism
        await self.session.write(req)
        self._increment_frame_number()

    async def read(self):
        res = await self.session.readuntil(TAIL)
        # strip HEAD, frame number and TAIL
        res = res[len(HEAD) + 1:-len(TAIL)]
        return res
