import asyncio
import contextlib
import logging
from typing import Callable, Optional

from skydance.protocol import (
    RESPONSE_HEADER_LENGTH,
    Command,
    FrameError,
    Response,
    State,
    frame_length,
)


log = logging.getLogger(__name__)


class Session:
    """
    A session object handling connection re-creation in case of its failure.

    A relay answers every command with a frame carrying the same frame number
    and the command type, so each request is paired with its reply. It is
    however a cheap Wi-Fi controller: it may stop answering at any time, or
    drop the TCP session without a notice. Therefore every exchange is bounded
    by a timeout and a failed exchange closes the socket, so that the next
    command opens a fresh one instead of hanging forever.
    """

    CONNECT_TIMEOUT = 5.0
    """Seconds to wait for a TCP connection to the relay."""

    COMMAND_TIMEOUT = 3.0
    """Seconds to wait for the relay to answer a single command."""

    CLOSE_TIMEOUT = 2.0
    """Seconds to wait for a connection to close."""

    PAUSE_BETWEEN_COMMANDS = 0.2
    """Seconds to wait between commands, the relay cannot handle them faster."""

    def __init__(self, host: str, port: int):
        """
        Create a Session.

        Args:
            host: A hostname or an IP address of the relay.
            port: A port of the relay.
        """
        self.host = host
        self.port = port

        self._state = State()
        self._lock = asyncio.Lock()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def request(self, command_factory: Callable[[State], Command]) -> bytes:
        """
        Send a command and wait for its reply.

        Commands are serialized: a command is sent only after the previous one
        has been answered (or has failed), because the relay does not handle
        concurrent requests well.

        Args:
            command_factory: A callable creating the command from a connection
                state. It is called under a lock, so the frame numbers of
                concurrent callers never clash, and it is called again with a
                fresh frame number when the command is retried.

        Return:
            Raw bytes of the reply frame.

        Raise:
            FrameError: If the relay answered with a malformed frame.
            OSError: If the connection to the relay failed.
        """
        async with self._lock:
            # Fail fast when the relay is not reachable at all: retrying a
            # failed connect would only make the caller wait longer.
            await self._ensure_connection()

            try:
                reply = await self._exchange(command_factory)
            except (asyncio.TimeoutError, OSError, EOFError, FrameError) as e:
                log.debug(
                    "Exchange with %s:%d failed (%r), reconnecting",
                    self.host,
                    self.port,
                    e,
                )
                await self._close_connection()
                # A single attempt on a fresh connection, no further retries.
                await self._ensure_connection()
                reply = await self._exchange(command_factory)

            await asyncio.sleep(self.PAUSE_BETWEEN_COMMANDS)
            return reply

    async def _exchange(self, command_factory: Callable[[State], Command]) -> bytes:
        command = command_factory(self._state)
        frame = command.raw
        expected_number = self._state.frame_number[0]
        # The frame number is used up as soon as the frame is built: when the
        # write gets cancelled half-way, the frame may still have been sent.
        self._state.increment_frame_number()

        log.debug("Sending: %s", frame.hex(" "))
        reply = await asyncio.wait_for(
            self._write_and_read(frame, expected_number, command.response_type),
            self.COMMAND_TIMEOUT,
        )
        log.debug("Received: %s", reply.hex(" "))
        return reply

    async def _write_and_read(
        self,
        frame: bytes,
        expected_number: int,
        expected_type: Optional[int],
    ) -> bytes:
        if self._writer is None:
            raise ConnectionError("Session is not connected.")
        self._writer.write(frame)
        await self._writer.drain()
        return await self._read_reply(expected_number, expected_type)

    async def _read_reply(
        self,
        expected_number: int,
        expected_type: Optional[int],
    ) -> bytes:
        while True:
            raw = await self._read_frame()
            response = Response(raw)

            if response.frame_number != expected_number:
                log.debug("Skipping a reply to another request: %s", raw.hex(" "))
                continue

            if expected_type is not None and response.cmd_type != expected_type:
                log.debug("Skipping a reply of another type: %s", raw.hex(" "))
                continue

            return raw

    async def _read_frame(self) -> bytes:
        if self._reader is None:
            raise ConnectionError("Session is not connected.")

        header = await self._reader.readexactly(RESPONSE_HEADER_LENGTH)
        length = frame_length(header)
        body = await self._reader.readexactly(length - RESPONSE_HEADER_LENGTH)
        return header + body

    async def _ensure_connection(self) -> None:
        if (
            self._writer is not None
            and not self._writer.is_closing()
            and self._reader is not None
        ):
            return

        await self._close_connection()

        log.debug("Opening connection to: %s:%d", self.host, self.port)
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            self.CONNECT_TIMEOUT,
        )

    async def _close_connection(self) -> None:
        writer, self._writer = self._writer, None
        self._reader = None

        if writer is None:
            return

        log.debug("Closing connection to: %s:%d", self.host, self.port)
        writer.close()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(writer.wait_closed(), self.CLOSE_TIMEOUT)

    async def close(self):
        """Close connection."""
        async with self._lock:
            await self._close_connection()

    async def __aenter__(self):
        """Return auto-closing context manager."""
        await self._ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
