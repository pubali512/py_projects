from datetime import datetime

from common.protocol import Protocol
from server.chat_logger import ChatLogger
from server.user_registry import UserRegistry


class MessageRouter:
    """Routes outgoing messages between connected clients and coordinates chat logging.

    Responsibilities:
        - Broadcast messages: log the message and deliver it to every connected client.
        - Direct messages: log the message and deliver it to the recipient.
        - Presence announcements: send the updated user list and system text to all clients.
    """

    def __init__(self, registry: UserRegistry, logger: ChatLogger) -> None:
        """
        :param registry: User registry used to find send targets.
        :type registry: UserRegistry
        :param logger: Logger for saving messages to disk.
        :type logger: ChatLogger
        :return: None
        :rtype: None
        """
        self._registry = registry
        self._logger = logger

    def route_broadcast(self, sender: str, text: str) -> None:
        """
        Save and send a message to every connected client.

        :param sender: Username of the sender.
        :type sender: str
        :param text: Message text.
        :type text: str
        :return: None
        :rtype: None
        """
        timestamp = datetime.now().isoformat(timespec="seconds")
        self._logger.save_broadcast_message(sender, text, timestamp)
        data = Protocol.make_server_msg(Protocol.TARGET_BROADCAST, sender, text, timestamp)
        self._registry.broadcast(data)

    def route_direct(self, sender: str, target: str, text: str) -> None:
        """
        Save and send a private message to the recipient and a copy to the sender.

        If the recipient is offline the message is still saved for their next login.

        :param sender: Username of the sender.
        :type sender: str
        :param target: Username of the recipient.
        :type target: str
        :param text: Message text.
        :type text: str
        :return: None
        :rtype: None
        """
        timestamp = datetime.now().isoformat(timespec="seconds")
        self._logger.save_dm_message(sender, target, text, timestamp)
        data = Protocol.make_server_msg(target, sender, text, timestamp)
        self._registry.send_to_user(target, data)
        if sender != target:
            self._registry.send_to_user(sender, data)

    def broadcast_users_list(self) -> None:
        """
        Send the current online user list to all clients.

        :return: None
        :rtype: None
        """
        users = self._registry.get_all_usernames()
        data = Protocol.make_users(users)
        self._registry.broadcast(data)

    def _send_users_list_to(self, username: str) -> None:
        """
        Send the current online user list to one specific client.

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
        Send a system notification to all connected clients.

        :param text: Notification text (e.g., 'Alice joined the chat').
        :type text: str
        :return: None
        :rtype: None
        """
        timestamp = datetime.now().isoformat(timespec="seconds")
        data = Protocol.make_sys(text, timestamp)
        self._registry.broadcast(data)
