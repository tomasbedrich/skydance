import asyncio
import contextlib
import logging
from typing import Tuple


log = logging.getLogger(__name__)


class Session:
    """A session object handling connection re-creation in case of its failure."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._connection = None
        self._write_lock = asyncio.Lock()
        self._read_lock = asyncio.Lock()

    async def _get_connection(
        self,
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if self._connection is None:
            log.debug("Opening connection to: %s:%d", self.host, self.port)
            self._connection = await asyncio.open_connection(self.host, self.port)
        return self._connection

    async def _close_connection(self) -> None:
        if self._connection:
            log.debug("Closing connection to: %s:%d", self.host, self.port)
            _, writer = self._connection
            writer.close()
            with contextlib.suppress(ConnectionError, TimeoutError):
                await writer.wait_closed()
            self._connection = None

    async def write(self, data: bytes):
        """
        Write a data to the transport and drain immediatelly.

        This is a wrapper on top of
        [`asyncio.streams.StreamWriter.write()`](https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter.write)
        """
        async with self._write_lock:
            while True:
                try:
                    _, writer = await self._get_connection()
                    log.debug("Sending: %s", data.hex(" "))
                    writer.write(data)
                    await writer.drain()
                    return
                except (ConnectionResetError, ConnectionAbortedError):
                    await self._close_connection()

    async def read(self, n=-1) -> bytes:
        """
        Read up to `n` bytes from the transport.

        This is a wrapper on top of
        [`asyncio.streams.StreamReader.read()`](https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamReader.read)
        """
        async with self._read_lock:
            while True:
                try:
                    reader, _ = await self._get_connection()
                    res = await reader.read(n)
                    log.debug("Received: %s", res.hex(" "))
                    return res
                except (ConnectionResetError, ConnectionAbortedError):
                    await self._close_connection()

    async def close(self):
        """Close connection."""
        await self._close_connection()

    async def __aenter__(self):
        """Return auto-closing context manager."""
        await self._get_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
