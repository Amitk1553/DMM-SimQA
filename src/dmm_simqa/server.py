"""Thread-per-connection TCP service for a shared SCPI instrument."""
import argparse
from contextlib import suppress
import logging
import socketserver
import threading
from typing import cast

from .instrument import VirtualDMM
from .scpi_parser import SCPIParser

LOG = logging.getLogger(__name__)
MAX_FRAME = 4096


class _Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        service = cast(_Listener, self.server)
        pending = bytearray()
        self.request.settimeout(0.25)
        with suppress(OSError):
            while not service.stopping.is_set():
                try:
                    chunk = self.request.recv(MAX_FRAME)
                except TimeoutError:
                    continue
                if not chunk:
                    return
                pending.extend(chunk)
                while (end := pending.find(b"\n")) >= 0:
                    if end >= MAX_FRAME:
                        return
                    frame = pending[:end]
                    del pending[:end + 1]
                    try:
                        command = frame.decode("ascii")
                    except UnicodeDecodeError:
                        command = ""  # Record a syntax error for this frame.
                    result = service.parser.execute(command)
                    if result is not None:
                        self.request.sendall((result + "\n").encode("ascii"))
                if len(pending) >= MAX_FRAME:
                    return


class _Listener(socketserver.ThreadingTCPServer):
    """Workers periodically check the stop event even during partial frames."""

    def __init__(self, address: tuple[str, int], parser: SCPIParser) -> None:
        self.parser = parser
        self.stopping = threading.Event()
        super().__init__(address, _Handler)


class SCPIServer:
    """Bind on start, expose the assigned port and join workers on stop."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5025) -> None:
        self.host = host
        self._requested_port = self.port = port
        self.instrument = VirtualDMM()
        self.parser = SCPIParser(self.instrument)
        self._listener: _Listener | None = None
        self._lifecycle = threading.Lock()

    def start(self) -> None:
        """Start listening in the background. Repeated starts are harmless."""
        with self._lifecycle:
            if self._listener is not None:
                return
            listener = _Listener((self.host, self._requested_port), self.parser)
            self.port = listener.server_address[1]
            self._thread = threading.Thread(target=listener.serve_forever,
                                            args=(0.05,), name="scpi-listener")
            try:
                self._thread.start()
            except RuntimeError:
                listener.server_close()
                raise
            self._listener = listener
            LOG.info("Listening on %s:%s", self.host, self.port)

    def stop(self) -> None:
        """Stop accepting, unblock connected clients and release the port."""
        with self._lifecycle:
            listener = self._listener
            if listener is None:
                return
            listener.stopping.set()
            listener.shutdown()
            self._thread.join()
            listener.server_close()
            self._listener = None


def main() -> None:
    """Run until interrupted by Ctrl+C."""
    options = argparse.ArgumentParser(description=__doc__)
    options.add_argument("--port", type=int, default=5025)
    args = options.parse_args()
    logging.basicConfig(level=logging.INFO)
    server = SCPIServer(port=args.port)
    server.start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


if __name__ == "__main__":
    main()
