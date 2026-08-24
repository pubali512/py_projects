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
        Serialize `payload` to a newline-terminated UTF-8 JSON message.

        :param payload: Message data to serialize.
        :type payload: dict
        :return: Newline-terminated JSON bytes.
        :rtype: bytes
        """
        return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

    @staticmethod
    def decode(line: str) -> dict:
        """
        Parse a JSON protocol line into a payload dict.

        :param line: A single JSON string from the socket.
        :type line: str
        :return: Parsed payload.
        :rtype: dict
        """
        return json.loads(line.strip())

    # Client -> Server factories

    @staticmethod
    def make_login(username: str) -> bytes:
        """
        Build a LOGIN packet for the given username.

        :param username: Username to register.
        :type username: str
        :return: Encoded LOGIN bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_LOGIN, "username": username})

    @staticmethod
    def make_client_msg(target: str, text: str) -> bytes:
        """
        Build a MSG packet to send from client to server.

        :param target: 'BROADCAST' or a username for a DM.
        :type target: str
        :param text: Message text.
        :type text: str
        :return: Encoded MSG bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_MSG, "target": target, "text": text})

    @staticmethod
    def make_logout() -> bytes:
        """
        Build a LOGOUT packet.

        :return: Encoded LOGOUT bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_LOGOUT})

    # Server -> Client factories

    @staticmethod
    def make_login_ok(users: list, history: dict) -> bytes:
        """
        Build a LOGIN_OK packet with the user list and full chat history.

        :param users: Currently connected usernames, including the new user.
        :type users: list
        :param history: Dict mapping conversation key to list of messages.
            'BROADCAST' for the public channel; a username for DMs.
        :type history: dict
        :return: Encoded LOGIN_OK bytes.
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
        Build a LOGIN_ERR packet with a reason string.

        :param reason: Why the login was rejected.
        :type reason: str
        :return: Encoded LOGIN_ERR bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_LOGIN_ERR, "reason": reason})

    @staticmethod
    def make_server_msg(target: str, sender: str, text: str, timestamp: str) -> bytes:
        """
        Build a routed MSG packet to send from server to one or more clients.

        :param target: 'BROADCAST' or the recipient username for DMs.
        :type target: str
        :param sender: Username of the message author.
        :type sender: str
        :param text: Message text.
        :type text: str
        :param timestamp: ISO-8601 timestamp set by the server.
        :type timestamp: str
        :return: Encoded MSG bytes.
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
        Build a USERS packet with the current online list.

        :param users: Currently online usernames.
        :type users: list
        :return: Encoded USERS bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_USERS, "users": users})

    @staticmethod
    def make_sys(text: str, timestamp: str) -> bytes:
        """
        Build a SYS notification packet (e.g., 'Alice joined the chat').

        :param text: Notification text.
        :type text: str
        :param timestamp: ISO-8601 timestamp.
        :type timestamp: str
        :return: Encoded SYS bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_SYS, "text": text, "timestamp": timestamp})
