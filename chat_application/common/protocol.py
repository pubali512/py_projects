import json


class Protocol:
    """Message type constants and encode/decode helpers for the chat protocol.

    All messages are newline-terminated JSON objects transmitted over TCP.
    Client-to-server and server-to-client message shapes differ; factory methods
    document each direction explicitly.

    Message types:
        LOGIN       client -> server: login request
        LOGIN_OK    server -> client: login accepted, carries users list and history
        LOGIN_ERR   server -> client: login rejected, carries reason string
        MSG         bidirectional: chat message (broadcast or direct)
        USERS       server -> client: updated list of online usernames
        SYS         server -> client: system notification text
        LOGOUT      client -> server: graceful disconnect
    """

    TYPE_LOGIN = "LOGIN"
    TYPE_LOGIN_OK = "LOGIN_OK"
    TYPE_LOGIN_ERR = "LOGIN_ERR"
    TYPE_MSG = "MSG"
    TYPE_USERS = "USERS"
    TYPE_SYS = "SYS"
    TYPE_LOGOUT = "LOGOUT"

    TARGET_BROADCAST = "BROADCAST"

    @staticmethod
    def encode(payload: dict) -> bytes:
        """Serialize a payload dict to a newline-terminated UTF-8 JSON bytes message."""
        return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

    @staticmethod
    def decode(line: str) -> dict:
        """Deserialize a JSON string (one protocol line) to a payload dict."""
        return json.loads(line.strip())

    # Client -> Server factories

    @staticmethod
    def make_login(username: str) -> bytes:
        """Login request sent by client."""
        return Protocol.encode({"type": Protocol.TYPE_LOGIN, "username": username})

    @staticmethod
    def make_client_msg(target: str, text: str) -> bytes:
        """Chat message sent by client to server (no sender or timestamp field)."""
        return Protocol.encode({"type": Protocol.TYPE_MSG, "target": target, "text": text})

    @staticmethod
    def make_logout() -> bytes:
        """Graceful disconnect request sent by client."""
        return Protocol.encode({"type": Protocol.TYPE_LOGOUT})

    # Server -> Client factories

    @staticmethod
    def make_login_ok(users: list, history: dict) -> bytes:
        """Login approval with current user list and full chat history for this session.

        Args:
            users: List of currently connected usernames (including the new user).
            history: Dict mapping conversation key to list of message dicts.
                     Keys: 'BROADCAST' for the public channel, or a username for DMs.
        """
        return Protocol.encode({
            "type": Protocol.TYPE_LOGIN_OK,
            "users": users,
            "history": history
        })

    @staticmethod
    def make_login_err(reason: str) -> bytes:
        """Login rejection with a human-readable reason."""
        return Protocol.encode({"type": Protocol.TYPE_LOGIN_ERR, "reason": reason})

    @staticmethod
    def make_server_msg(target: str, sender: str, text: str, timestamp: str) -> bytes:
        """Routed chat message sent from server to client(s).

        Args:
            target: 'BROADCAST' or the recipient username for DMs.
            sender: Username of the message author.
            text: Message body (emoji shortcodes already replaced by client).
            timestamp: ISO-8601 timestamp string set by the server.
        """
        return Protocol.encode({
            "type": Protocol.TYPE_MSG,
            "target": target,
            "sender": sender,
            "text": text,
            "timestamp": timestamp
        })

    @staticmethod
    def make_users(users: list) -> bytes:
        """Broadcast updated list of online usernames to all clients."""
        return Protocol.encode({"type": Protocol.TYPE_USERS, "users": users})

    @staticmethod
    def make_sys(text: str, timestamp: str) -> bytes:
        """System notification (e.g., 'Alice joined the chat')."""
        return Protocol.encode({"type": Protocol.TYPE_SYS, "text": text, "timestamp": timestamp})
