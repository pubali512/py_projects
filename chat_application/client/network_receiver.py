import socket
import threading

from common.protocol import Protocol


class NetworkReceiver:
    """Reads incoming protocol messages from the server socket in a background thread.

    The receiver runs as a daemon thread so it is automatically terminated when
    the main process exits. Incoming messages are delivered via on_message_callback
    (called from the background thread). GUI code must dispatch these callbacks to
    the main thread using root.after().

    The on_disconnect_callback is called exactly once when the connection is lost,
    either due to a network error or because stop() was called.
    """

    def __init__(self, client_socket: socket.socket, on_message_callback: callable, on_disconnect_callback: callable):
        """Args:
            client_socket: The connected TCP socket to the server.
            on_message_callback: Called with a parsed payload dict for each received message.
            on_disconnect_callback: Called (with no arguments) when the socket closes.
        """
        self._socket = client_socket
        self._on_message = on_message_callback
        self._on_disconnect = on_disconnect_callback
        self._is_running = False
        self._thread = threading.Thread(target=self.receive_loop, daemon=True)

    def start(self):
        """Start the background receiving thread."""
        self._is_running = True
        self._thread.start()

    def stop(self):
        """Signal the receiving loop to stop on its next iteration."""
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """True while the background receiver thread is active."""
        return self._is_running

    def receive_loop(self):
        """Continuously read newline-delimited JSON messages from the server socket.

        Malformed JSON lines are silently skipped. The loop exits on socket error,
        EOF, or when stop() has been called.
        """
        socket_file = self._socket.makefile("r", encoding="utf-8")
        try:
            for line in socket_file:
                if not self._is_running:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = Protocol.decode(line)
                    self._on_message(payload)
                except ValueError:
                    continue
        except (OSError, ConnectionError):
            pass
        finally:
            socket_file.close()
            self._is_running = False
            self._on_disconnect()
