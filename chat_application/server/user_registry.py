class UserRegistry:
    """Tracks all currently connected and authenticated users.

    Maps each username to a send callable supplied by the corresponding
    ClientHandler. Using a callable keeps the registry decoupled from socket
    details.
    """

    def __init__(self) -> None:
        self._users: dict[str, callable] = {}

    def add_user(self, username: str, send_fn: callable) -> None:
        """
        Register an authenticated user with their thread-safe send function.

        :param username: The validated, unique handle for this session.
        :type username: str
        :param send_fn: Callable(bytes) that writes data to the user's socket.
        :type send_fn: callable
        :return: None
        :rtype: None
        """
        self._users[username] = send_fn

    def remove_user(self, username: str) -> bool:
        """
        Deregister a user.

        :param username: The handle to remove.
        :type username: str
        :return: True if the user was present and removed, False if not found.
        :rtype: bool
        """
        return self._users.pop(username, None) is not None

    def is_active(self, username: str) -> bool:
        """
        Return True if the username is currently registered.

        :param username: The handle to check.
        :type username: str
        :return: True if the user is currently connected.
        :rtype: bool
        """
        return username in self._users

    def get_all_usernames(self) -> list[str]:
        """
        Return a snapshot list of all currently connected usernames.

        :return: List of currently connected username strings.
        :rtype: list[str]
        """
        return list(self._users.keys())

    def send_to_user(self, username: str, data: bytes) -> bool:
        """
        Send raw bytes to a specific user.

        :param username: Target handle.
        :type username: str
        :param data: Encoded protocol message bytes.
        :type data: bytes
        :return: True if the user was found and data was sent successfully.
        :rtype: bool
        """
        send_fn = self._users.get(username)
        if send_fn is None:
            return False
        try:
            send_fn(data)
            return True
        except OSError:
            return False

    def broadcast(self, data: bytes, exclude: str = None) -> None:
        """
        Send data to every registered user, optionally skipping one.

        :param data: Encoded protocol message bytes.
        :type data: bytes
        :param exclude: Username to skip, or None to send to all.
        :type exclude: str
        :return: None
        :rtype: None
        """
        recipients = [u for u in self._users if u != exclude]
        for username in recipients:
            self.send_to_user(username, data)
