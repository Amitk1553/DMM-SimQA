"""Synchronous context-managed SCPI session."""
import socket
from types import TracebackType
from typing import BinaryIO


class SCPIClient:
    """Use one client per thread. A transport failure closes the session."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5025,
                 timeout: float = 3.0) -> None:
        self.address = (host, port)
        self.timeout = timeout
        self._socket: socket.socket | None = None
        self._reader: BinaryIO | None = None

    def __enter__(self) -> "SCPIClient":
        if self._socket is not None:
            raise RuntimeError("Session already connected")
        self._socket = socket.create_connection(self.address, self.timeout)
        self._reader = self._socket.makefile("rb")
        return self

    def close(self) -> None:
        """Release buffered and socket resources."""
        if self._reader is not None:
            self._reader.close()
            self._reader = None
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc: BaseException | None, tb: TracebackType | None) -> None:
        self.close()

    def write(self, cmd: str) -> None:
        """Send one ASCII command with an LF terminator."""
        if self._socket is None:
            raise RuntimeError("Open a client session first")
        cmd = cmd.rstrip("\r\n")
        if "\r" in cmd or "\n" in cmd:
            raise ValueError("Expected one command")
        try:
            self._socket.sendall((cmd + "\n").encode("ascii"))
        except OSError:
            self.close()
            raise

    def query(self, cmd: str) -> str:
        """Send a query and read its complete response within the timeout."""
        self.write(cmd)
        assert self._reader is not None
        try:
            frame = self._reader.readline(4097)
            if not frame.endswith(b"\n") or len(frame) > 4096:
                raise ConnectionError("Incomplete or oversized response")
            return frame.decode("ascii").rstrip("\r\n")
        except (OSError, UnicodeError):
            self.close()
            raise
