import socket

from client.network_receiver import NetworkReceiver
from common.protocol import Protocol


class ChatClient:
    """Manages the TCP connection to the chat server and all outgoing message sends.

    Connection lifecycle:
        1. connect(username) establishes the socket, starts NetworkReceiver, and
           sends the LOGIN message. 
        2. send_message() can be called at any time after a successful connection.
        3. disconnect() sends LOGOUT, stops the receiver, and closes the socket.
    """

    CONNECTION_TIMEOUT_SECONDS = 5.0

    def __init__(self, host: str, port: int, on_message: callable, on_disconnect: callable) -> None:
        """
        :param host: Server hostname or IP address.
        :type host: str
        :param port: Server TCP port.
        :type port: int
        :param on_message: Called with each incoming server message payload.
            Runs on the background receive thread.
        :type on_message: callable
        :param on_disconnect: Called with no arguments when the connection closes.
        :type on_disconnect: callable
        :return: None
        :rtype: None
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
        """
        Open a TCP connection and send the login request.

        The server's response (LOGIN_OK or LOGIN_ERR) arrives via the message
        callback, not directly from this method.

        :param username: Username to register on the server.
        :type username: str
        :return: (True, None) on success; (False, error message) if connection failed.
        :rtype: tuple[bool, str]
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
            on_disconnect_callback=self._handle_network_disconnect,
        )
        self._receiver.start()

        self._socket.sendall(Protocol.make_login(username))
        return True, None

    def disconnect(self) -> None:
        """
        Send a LOGOUT message and close the socket.

        :return: None
        :rtype: None
        """
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

    def send_message(self, target: str, text: str) -> None:
        """
        Send a chat message to a target channel or user.

        :param target: 'BROADCAST' or a username for a DM.
        :type target: str
        :param text: Message text with emoji shortcodes already replaced.
        :type text: str
        :return: None
        :rtype: None
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
        """
        True if a server connection is active.
        """
        return self._connected

    @property
    def username(self) -> str:
        """
        The username used for the current or last connection.
        """
        return self._username

    def _handle_network_disconnect(self) -> None:
        """
        Called when the socket drops. Notifies the disconnect callback.

        :return: None
        :rtype: None
        """
        if self._connected:
            self._connected = False
            self._on_disconnect()
