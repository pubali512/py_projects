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
        """
        Serialize a payload dict to a newline-terminated UTF-8 JSON bytes message.

        :param payload: The message data to serialize.
        :type payload: dict
        :return: Newline-terminated UTF-8 encoded JSON bytes.
        :rtype: bytes
        """
        return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

    @staticmethod
    def decode(line: str) -> dict:
        """
        Deserialize a JSON string (one protocol line) to a payload dict.

        :param line: A single newline-delimited JSON string.
        :type line: str
        :return: Parsed message payload.
        :rtype: dict
        """
        return json.loads(line.strip())

    # Client -> Server factories

    @staticmethod
    def make_login(username: str) -> bytes:
        """
        Build a LOGIN request packet to send to the server.

        :param username: The handle to register on the server.
        :type username: str
        :return: Encoded LOGIN message bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_LOGIN, "username": username})

    @staticmethod
    def make_client_msg(target: str, text: str) -> bytes:
        """
        Build a chat message packet to send from client to server.

        :param target: 'BROADCAST' for the public channel, or a username for a DM.
        :type target: str
        :param text: Message body with emoji shortcodes already replaced.
        :type text: str
        :return: Encoded MSG message bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_MSG, "target": target, "text": text})

    @staticmethod
    def make_logout() -> bytes:
        """
        Build a LOGOUT packet for a graceful client disconnect.

        :return: Encoded LOGOUT message bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_LOGOUT})

    # Server -> Client factories

    @staticmethod
    def make_login_ok(users: list, history: dict) -> bytes:
        """
        Build a LOGIN_OK approval packet with the current user list and chat history.

        :param users: List of currently connected usernames (including the new user).
        :type users: list
        :param history: Dict mapping conversation key to list of message dicts.
            Keys: 'BROADCAST' for the public channel, or a username for DMs.
        :type history: dict
        :return: Encoded LOGIN_OK message bytes.
        :rtype: bytes
        """
        return Protocol.encode({
            "type": Protocol.TYPE_LOGIN_OK,
            "users": users,
            "history": history
        })

    @staticmethod
    def make_login_err(reason: str) -> bytes:
        """
        Build a LOGIN_ERR rejection packet with a human-readable reason.

        :param reason: Description of why the login was rejected.
        :type reason: str
        :return: Encoded LOGIN_ERR message bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_LOGIN_ERR, "reason": reason})

    @staticmethod
    def make_server_msg(target: str, sender: str, text: str, timestamp: str) -> bytes:
        """
        Build a routed chat message packet sent from server to client(s).

        :param target: 'BROADCAST' or the recipient username for DMs.
        :type target: str
        :param sender: Username of the message author.
        :type sender: str
        :param text: Message body with emoji shortcodes already replaced by the client.
        :type text: str
        :param timestamp: ISO-8601 timestamp string set by the server.
        :type timestamp: str
        :return: Encoded MSG message bytes.
        :rtype: bytes
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
        """
        Build a USERS packet to broadcast the updated list of online usernames.

        :param users: List of currently online usernames.
        :type users: list
        :return: Encoded USERS message bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_USERS, "users": users})

    @staticmethod
    def make_sys(text: str, timestamp: str) -> bytes:
        """
        Build a SYS notification packet (e.g., 'Alice joined the chat').

        :param text: Human-readable notification text.
        :type text: str
        :param timestamp: ISO-8601 timestamp string.
        :type timestamp: str
        :return: Encoded SYS message bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_SYS, "text": text, "timestamp": timestamp})
