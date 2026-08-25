import json


class Protocol:
    """This class implements the simple communicattion protocol the client and server use to communicate.

    
    Each message exchanged between a client and the server has a special purpose 
    (e.g., a login message from the client is different from a chat message). Therefore, 
    additional information (e.g., the type of the message, the sender of the message 
    etc.) are transmitted along with the actual message's payload. This entire 
    message (payload + additional information) is represented as a Python dict, which is 
    converted to a JSON string before transmitting it over the TCP socket. 
    
    On the receiving end, the JSON string is converted back to a Python dict, and the 
    message type is used to determine how to handle the message (e.g., allow users to login, 
    or forward a DM to another user etc.). 

    Message types:
        LOGIN       client -> server: login request
        LOGIN_OK    server -> client: login accepted, carries users list and history
        LOGIN_ERR   server -> client: login rejected, carries reason string
        MSG         client <-> server: chat message (broadcast or DM between two users)
        USERS       server -> client: updated list of online usernames
        SYS         server -> client: system notification text
        LOGOUT      client -> server: disconnect
    """

    TYPE_LOGIN = "LOGIN"
    TYPE_LOGIN_OK = "LOGIN_OK"
    TYPE_LOGIN_ERR = "LOGIN_ERR"
    TYPE_MSG = "MSG"
    TYPE_USERS = "USERS"
    TYPE_SYS = "SYS"
    TYPE_LOGOUT = "LOGOUT"

    TARGET_BROADCAST = "BROADCAST"

    # Common methods 
    @staticmethod
    def encode(payload: dict) -> bytes:
        """
        Convert payload dict to a JSON message string for the communication socket.

        :param payload: Message data to be sent over the TCP socket.
        :type payload: dict
        :return: Newline-terminated JSON bytes.
        :rtype: bytes
        """
        return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

    @staticmethod
    def decode(line: str) -> dict:
        """
        Parse a JSON protocol line received from a socket into a payload dict.

        :param line: A single JSON string from the socket.
        :type line: str
        :return: Parsed payload.
        :rtype: dict
        """
        return json.loads(line.strip())
    

    # Creation of specific messages for communication between client and server
    
    # Client -> Server messages 
    @staticmethod
    def make_login(username: str) -> bytes:
        """
        Build a LOGIN packet (client->server) for the given username.

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

    # Server -> Client messages 

    @staticmethod
    def make_login_ok(users: list, history: dict) -> bytes:
        """
        Build a LOGIN_OK packet with the user list and full chat history.

        :param users: Currently connected usernames, including the new user.
        :type users: list
        :param history: Dict containing entire chat history (one list of messages per conversation).
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
        Build a message packet to send from server to one or more clients.

        :param target: 'BROADCAST' or the recipient username for DMs.
        :type target: str
        :param sender: Username of the message author.
        :type sender: str
        :param text: Message text.
        :type text: str
        :param timestamp: Timestamp set by the server.
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
        Build a USERS packet with the currently online user list.

        :param users: Currently online usernames.
        :type users: list
        :return: Encoded USERS bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_USERS, "users": users})

    @staticmethod
    def make_sys(text: str, timestamp: str) -> bytes:
        """
        Build a SYS notification packet (e.g., 'X joined the chat').

        :param text: Notification text.
        :type text: str
        :param timestamp: Timestamp of the message.
        :type timestamp: str
        :return: Encoded SYS bytes.
        :rtype: bytes
        """
        return Protocol.encode({"type": Protocol.TYPE_SYS, "text": text, "timestamp": timestamp})
