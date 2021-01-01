import asyncio
import logging
from typing import Tuple


log = logging.getLogger(__name__)


# TODO refactor this in order to incorporate SequentialWriter from home-assistant-skydance


class Connection:
    """A singleton wrapper for connection (a tuple of StreamReader, StreamWriter) to given host and port."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._connection = None

    async def get(
        self,
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if self._connection is None:
            log.debug("Opening connection to: %s:%d", self.host, self.port)
            self._connection = await asyncio.open_connection(self.host, self.port)
        return self._connection

    async def close(self):
        if self._connection:
            log.debug("Closing connection to: %s:%d", self.host, self.port)
            _, writer = self._connection
            writer.close()
            await writer.wait_closed()
            self._connection = None


class Session:
    """A session object handling connection re-creation in case of its failure."""

    def __init__(self, connection: Connection):
        self._connection = connection
        self._write_lock = asyncio.Lock()
        self._read_lock = asyncio.Lock()

    async def write(self, data: bytes):
        """
        Write a data to the transport and drain immediatelly.

        This is a wrapper on top of
        [`asyncio.streams.StreamWriter.write()`](https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter.write)
        """
        async with self._write_lock:
            while True:
                try:
                    _, writer = await self._connection.get()
                    log.debug("Sending: %s", data.hex(" "))
                    writer.write(data)
                    await writer.drain()
                    return
                except (ConnectionResetError, ConnectionAbortedError):
                    await self._connection.close()

    async def read(self, n=-1) -> bytes:
        """
        Read up to `n` bytes from the transport.

        This is a wrapper on top of
        [`asyncio.streams.StreamReader.read()`](https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamReader.read)
        """
        async with self._read_lock:
            while True:
                try:
                    reader, _ = await self._connection.get()
                    res = await reader.read(n)
                    log.debug("Received: %s", res.hex(" "))
                    return res
                except (ConnectionResetError, ConnectionAbortedError):
                    await self._connection.close()

    async def close(self):
        """Close connection."""
        await self._connection.close()

    async def __aenter__(self):
        """Return auto-closing context manager."""
        await self._connection.get()  # prepare connection not to slow down first write()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
