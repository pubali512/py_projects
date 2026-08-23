from datetime import datetime

from common.protocol import Protocol
from server.chat_persistence import ChatPersistence
from server.user_registry import UserRegistry


class MessageRouter:
    """Routes outgoing messages between connected clients and coordinates persistence.

    Responsibilities:
        - Broadcast messages: persist then deliver to every connected client.
        - Direct messages: persist then deliver to recipient and reflect to sender.
        - Presence announcements: send updated user list and system text to all clients.
    """

    def __init__(self, registry: UserRegistry, persistence: ChatPersistence) -> None:
        """
        Initialize the router with the shared registry and persistence services.

        :param registry: The active user registry used to resolve send targets.
        :type registry: UserRegistry
        :param persistence: The persistence layer used to save messages to disk.
        :type persistence: ChatPersistence
        :return: None
        :rtype: None
        """
        self._registry = registry
        self._persistence = persistence

    def route_broadcast(self, sender: str, text: str) -> None:
        """
        Persist a broadcast message and deliver it to all connected clients.

        :param sender: Username of the originating client.
        :type sender: str
        :param text: Message body with emoji shortcodes already replaced by the client.
        :type text: str
        :return: None
        :rtype: None
        """
        timestamp = datetime.now().isoformat(timespec="seconds")
        self._persistence.save_broadcast_message(sender, text, timestamp)
        data = Protocol.make_server_msg(Protocol.TARGET_BROADCAST, sender, text, timestamp)
        self._registry.broadcast(data)

    def route_direct(self, sender: str, target: str, text: str) -> None:
        """
        Persist a direct message and deliver it to recipient and sender.

        If the target is not currently connected the message is still persisted so
        that the target will receive it as history on their next login.

        :param sender: Username of the originating client.
        :type sender: str
        :param target: Username of the intended recipient.
        :type target: str
        :param text: Message body.
        :type text: str
        :return: None
        :rtype: None
        """
        timestamp = datetime.now().isoformat(timespec="seconds")
        self._persistence.save_dm_message(sender, target, text, timestamp)
        data = Protocol.make_server_msg(target, sender, text, timestamp)
        self._registry.send_to_user(target, data)
        if sender != target:
            self._registry.send_to_user(sender, data)

    def broadcast_users_list(self) -> None:
        """
        Send the current online user list to every connected client.

        :return: None
        :rtype: None
        """
        users = self._registry.get_all_usernames()
        data = Protocol.make_users(users)
        self._registry.broadcast(data)

    def send_users_list_to(self, username: str) -> None:
        """
        Send the current online user list to a single client.

        :param username: The recipient username.
        :type username: str
        :return: None
        :rtype: None
        """
        users = self._registry.get_all_usernames()
        data = Protocol.make_users(users)
        self._registry.send_to_user(username, data)

    def broadcast_sys(self, text: str) -> None:
        """
        Broadcast a system notification to all connected clients.

        :param text: Human-readable system message (e.g., 'Alice joined the chat').
        :type text: str
        :return: None
        :rtype: None
        """
        timestamp = datetime.now().isoformat(timespec="seconds")
        data = Protocol.make_sys(text, timestamp)
        self._registry.broadcast(data)
