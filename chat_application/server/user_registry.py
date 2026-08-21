class UserRegistry:
    """Tracks all currently connected and authenticated users.

    Maps each username to a send callable supplied by the corresponding
    ClientHandler. Using a callable keeps the registry decoupled from socket
    details.
    """

    def __init__(self):
        self._users: dict[str, callable] = {}

    def add_user(self, username: str, send_fn: callable):
        """Register an authenticated user with their thread-safe send function.

        Args:
            username: The validated, unique handle for this session.
            send_fn: Callable(bytes) that writes data to the user's socket.
        """
        self._users[username] = send_fn

    def remove_user(self, username: str) -> bool:
        """Deregister a user.

        Returns:
            True if the user was present and removed, False if not found.
        """
        return self._users.pop(username, None) is not None

    def is_active(self, username: str) -> bool:
        """Return True if the username is currently registered."""
        return username in self._users

    def get_all_usernames(self) -> list[str]:
        """Return a snapshot list of all currently connected usernames."""
        return list(self._users.keys())

    def send_to_user(self, username: str, data: bytes) -> bool:
        """Send raw bytes to a specific user.

        Args:
            username: Target handle.
            data: Encoded protocol message bytes.

        Returns:
            True if the user was found and data was sent successfully.
        """
        send_fn = self._users.get(username)
        if send_fn is None:
            return False
        try:
            send_fn(data)
            return True
        except OSError:
            return False

    def broadcast(self, data: bytes, exclude: str = None):
        """Send data to every registered user, optionally skipping one.

        Args:
            data: Encoded protocol message bytes.
            exclude: Username to skip.
        """
        recipients = [u for u in self._users if u != exclude]
        for username in recipients:
            self.send_to_user(username, data)
