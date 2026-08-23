import socket

from common.protocol import Protocol
from common.username_validator import UsernameValidator
from server.chat_persistence import ChatPersistence
from server.message_router import MessageRouter
from server.user_registry import UserRegistry


class ClientHandler:
    """Handles all communication with a single connected client in a dedicated thread.

    Lifecycle:
        1. ClientHandler is created by ChatServer for each accepted connection.
        2. ChatServer starts the handler in a daemon thread via run().
        3. The handler reads protocol lines from the socket until the client
           disconnects or sends LOGOUT.
        4. On exit the handler removes the user from the registry and notifies
           remaining clients.

    Accepted message types (client -> server):
        LOGIN   Authenticate with a username. Must arrive before any MSG.
        MSG     Send a broadcast or direct message.
        LOGOUT  Graceful disconnect.
    """

    def __init__(
        self,
        client_socket: socket.socket,
        address: tuple,
        router: MessageRouter,
        registry: UserRegistry,
        persistence: ChatPersistence,
        validator: UsernameValidator,
    ) -> None:
        """
        Initialize the handler with the accepted socket and shared server services.

        :param client_socket: The accepted TCP socket for this client.
        :type client_socket: socket.socket
        :param address: (host, port) tuple of the remote peer.
        :type address: tuple
        :param router: Shared message router.
        :type router: MessageRouter
        :param registry: Shared user registry.
        :type registry: UserRegistry
        :param persistence: Shared chat persistence layer.
        :type persistence: ChatPersistence
        :param validator: Username validator (stateless, shared safely).
        :type validator: UsernameValidator
        :return: None
        :rtype: None
        """
        self._socket = client_socket
        self._address = address
        self._router = router
        self._registry = registry
        self._persistence = persistence
        self._validator = validator
        self._username: str = None

    # Used as the send callable stored in UserRegistry.

    def send(self, data: bytes) -> None:
        """
        Write bytes to this client's socket.

        :param data: Encoded protocol message bytes to deliver.
        :type data: bytes
        :return: None
        :rtype: None
        """
        try:
            self._socket.sendall(data)
        except OSError:
            pass

    # Message handlers

    def handle_login(self, payload: dict) -> None:
        """
        Process a LOGIN request: validate the username, register the user, and send history.

        :param payload: Decoded LOGIN message dict containing the 'username' field.
        :type payload: dict
        :return: None
        :rtype: None
        """
        username = payload.get("username", "")
        is_valid, reason = self._validator.validate(username)
        if not is_valid:
            self.send(Protocol.make_login_err(reason))
            return

        if self._registry.is_active(username):
            self.send(Protocol.make_login_err("Username is already taken"))
            return

        self._username = username
        self._registry.add_user(username, self.send)

        history = self._persistence.load_all_history_for_user(username)
        users = self._registry.get_all_usernames()
        self.send(Protocol.make_login_ok(users, history))

        self._router.broadcast_users_list()
        self._router.broadcast_sys(f"{username} joined the chat")

    def handle_message(self, payload: dict) -> None:
        """
        Route a broadcast or direct message from the authenticated client.

        :param payload: Decoded MSG message dict with 'target' and 'text' fields.
        :type payload: dict
        :return: None
        :rtype: None
        """
        if not self._username:
            return

        target = payload.get("target", "")
        text = payload.get("text", "").strip()
        if not text:
            return

        if target == Protocol.TARGET_BROADCAST:
            self._router.route_broadcast(self._username, text)
        else:
            self._router.route_direct(self._username, target, text)

    def cleanup(self) -> None:
        """
        Remove the user from the registry and notify remaining clients.

        :return: None
        :rtype: None
        """
        if self._username:
            was_registered = self._registry.remove_user(self._username)
            if was_registered:
                self._router.broadcast_users_list()
                self._router.broadcast_sys(f"{self._username} left the chat")
            self._username = None
        try:
            self._socket.close()
        except OSError:
            pass

    # Main thread entry point

    def run(self):
        """
        Read and process protocol messages until the client disconnects.

        This method is intended to be called inside a daemon thread.
        Malformed JSON lines are silently skipped; unexpected socket errors
        and graceful LOGOUT both terminate the loop cleanly.
        :return: None
        :rtype: None        """
        socket_file = self._socket.makefile("r", encoding="utf-8")
        try:
            for line in socket_file:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = Protocol.decode(line)
                except ValueError:
                    continue  # Skip malformed JSON

                msg_type = payload.get("type")
                if msg_type == Protocol.TYPE_LOGIN:
                    self.handle_login(payload)
                elif msg_type == Protocol.TYPE_MSG:
                    self.handle_message(payload)
                elif msg_type == Protocol.TYPE_LOGOUT:
                    break
        except (OSError, ConnectionError):
            pass
        finally:
            socket_file.close()
            self.cleanup()
