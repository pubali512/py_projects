import socket

from client.network_receiver import NetworkReceiver
from common.protocol import Protocol


class ChatClient:
    """Manages the TCP connection to the chat server and all outgoing message sends.

    Connection lifecycle:
        1. connect(username) establishes the socket, starts NetworkReceiver, and
           sends the LOGIN message. It returns immediately; the server's response
           (LOGIN_OK or LOGIN_ERR) is delivered asynchronously via on_message_callback.
        2. send_message() can be called at any time after a successful connection.
        3. disconnect() sends LOGOUT, stops the receiver, and closes the socket.

    Thread safety:
        send_message() and disconnect() are safe to call from the GUI (main) thread
        while the NetworkReceiver background thread is running.
    """

    CONNECTION_TIMEOUT_SECONDS = 5.0

    def __init__(self, host: str, port: int, on_message: callable, on_disconnect: callable):
        """Args:
            host: Server hostname or IP address.
            port: Server TCP port.
            on_message: Callback(payload: dict) invoked for every server message
                        (called from the background NetworkReceiver thread).
            on_disconnect: Callback() invoked when the connection is closed.
        """
        self._host = host
        self._port = port
        self._on_message = on_message
        self._on_disconnect = on_disconnect
        self._socket: socket.socket = None
        self._receiver: NetworkReceiver = None
        self._username: str = None
        self._connected = False

    def connect(self, username: str) -> tuple[bool, str]:
        """Open a TCP connection to the server and send the LOGIN message.

        The method returns as soon as the socket is established and the login
        request is sent. The caller should wait for LOGIN_OK or LOGIN_ERR via
        the on_message_callback to know whether authentication succeeded.

        Args:
            username: The handle to register on the server.

        Returns:
            (True, None) if the TCP connection was established.
            (False, error_message) if the connection could not be opened.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.CONNECTION_TIMEOUT_SECONDS)
            self._socket.connect((self._host, self._port))
            self._socket.settimeout(None)
        except (ConnectionRefusedError, socket.timeout, OSError) as error:
            return False, str(error)

        self._username = username
        self._connected = True

        self._receiver = NetworkReceiver(
            client_socket=self._socket,
            on_message_callback=self._on_message,
            on_disconnect_callback=self.handle_network_disconnect,
        )
        self._receiver.start()

        self._socket.sendall(Protocol.make_login(username))
        return True, None

    def disconnect(self):
        """Send LOGOUT and close the connection gracefully."""
        if not self._connected:
            return
        self._connected = False
        if self._receiver:
            self._receiver.stop()
        try:
            self._socket.sendall(Protocol.make_logout())
            self._socket.close()
        except OSError:
            pass
        self._on_disconnect()

    def send_message(self, target: str, text: str):
        """Send a chat message to the given target.

        Args:
            target: 'BROADCAST' for public channel, or a username for a DM.
            text: Message body (emoji shortcodes should be replaced before calling).
        """
        if not self._connected:
            return
        data = Protocol.make_client_msg(target, text)
        try:
            self._socket.sendall(data)
        except OSError:
            self._connected = False

    @property
    def is_connected(self) -> bool:
        """Return True if the client currently has an active server connection."""
        return self._connected

    @property
    def username(self) -> str:
        """Return the username used for the current (or last) connection."""
        return self._username

    def handle_network_disconnect(self):
        """Called by NetworkReceiver when the socket drops unexpectedly."""
        if self._connected:
            self._connected = False
            self._on_disconnect()
