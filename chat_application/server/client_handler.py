import socket

from common.protocol import Protocol
from common.username_validator import UsernameValidator
from server.chat_logger import ChatLogger
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
        persistence: ChatLogger,
        validator: UsernameValidator,
    ) -> None:
        """
        :param client_socket: The accepted TCP socket for this client.
        :type client_socket: socket.socket
        :param address: (host, port) of the remote peer.
        :type address: tuple
        :param router: Shared message router.
        :type router: MessageRouter
        :param registry: Shared user registry.
        :type registry: UserRegistry
        :param persistence: Shared chat persistence layer.
        :type persistence: ChatLogger
        :param validator: Username validator.
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
        Send bytes to this client.

        :param data: Encoded message bytes.
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
        Validate and register the user, then send welcome data.

        :param payload: Decoded LOGIN message dict with the 'username' field.
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
        Forward a chat message from this client to the right target.

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
        Unregister the user and notify the remaining clients.

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

    def run(self) -> None:
        """
        Read incoming messages in a loop until the client disconnects or sends LOGOUT.

        Incorrectly formatted JSON lines are skipped silently.

        :return: None
        :rtype: None
        """
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
