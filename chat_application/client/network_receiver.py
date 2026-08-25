import socket
import threading

from common.protocol import Protocol


class NetworkReceiver:
    """Reads incoming messages from the server socket in a background thread.

    This class delivers each incoming message to the GUI via on_message_callback.
    When the connection closes, on_disconnect_callback is called once.
    """

    def __init__(self, client_socket: socket.socket, on_message_callback: callable, on_disconnect_callback: callable) -> None:
        """
        :param client_socket: The connected TCP socket to the server.
        :type client_socket: socket.socket
        :param on_message_callback: Called with a parsed payload dict for each message.
        :type on_message_callback: callable
        :param on_disconnect_callback: Called with no arguments when the socket closes.
        :type on_disconnect_callback: callable
        :return: None
        :rtype: None
        """
        self._socket = client_socket
        self._on_message = on_message_callback
        self._on_disconnect = on_disconnect_callback
        self._is_running = False
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)

    def start(self) -> None:
        """
        Start the background receive thread.

        :return: None
        :rtype: None
        """
        self._is_running = True
        self._thread.start()

    def stop(self) -> None:
        """
        Signal the receive loop to stop.

        :return: None
        :rtype: None
        """
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """
        True while the receive thread is running.
        """
        return self._is_running

    def _receive_loop(self) -> None:
        """
        Read incoming JSON messages from the server in a loop.

        Incorrectly formatted lines are skipped. The loop exits on a
        socket error, end of stream, or when stop() is called.

        :return: None
        :rtype: None
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
