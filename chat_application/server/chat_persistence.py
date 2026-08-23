import glob
import json
import os


class ChatPersistence:
    """Reads and writes chat history to JSON files inside a chat_logs directory.

    File layout:
        chat_logs/broadcast.json          All public broadcast messages.
        chat_logs/dm-<a>-<b>.json         Direct-message thread between users a and b,
                                          where a and b are sorted alphabetically.
                                           The dash (-) separator is safe because usernames
                                           only allow letters, digits, and underscores.

    Each JSON file has a single top-level key 'messages' whose value is a list of
    message dicts. Only MSG-type messages are persisted; system notifications are not.

    Message dict shape:
        {"type": "MSG", "sender": str, "target": str, "text": str, "timestamp": str}
    """

    BROADCAST_FILE = "broadcast.json"
    LOGS_SUBDIR = "chat_logs"

    def __init__(self, base_dir: str) -> None:
        """
        Set up the chat logs directory, creating it if it does not yet exist.

        :param base_dir: Directory that contains (or will contain) the chat_logs folder.
            Typically the server/ package directory.
        :type base_dir: str
        :return: None
        :rtype: None
        """
        self._logs_dir = os.path.join(base_dir, self.LOGS_SUBDIR)
        os.makedirs(self._logs_dir, exist_ok=True)

    # Path helpers

    @property
    def broadcast_path(self) -> str:
        return os.path.join(self._logs_dir, self.BROADCAST_FILE)

    def dm_path(self, username1: str, username2: str) -> str:
        """
        Return the canonical file path for a DM thread, with names sorted alphabetically.

        :param username1: First participant username.
        :type username1: str
        :param username2: Second participant username.
        :type username2: str
        :return: Absolute path to the dm-<a>-<b>.json log file.
        :rtype: str
        """
        pair = sorted([username1, username2])
        return os.path.join(self._logs_dir, f"dm-{pair[0]}-{pair[1]}.json")

    # Low-level read/write

    def read_messages(self, filepath: str) -> list:
        """
        Return the messages list from a log file, or an empty list if the file does not exist.

        :param filepath: Absolute path to the JSON log file.
        :type filepath: str
        :return: List of message dicts read from the file.
        :rtype: list
        """
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        return data.get("messages", [])

    def append_message(self, filepath: str, message: dict) -> None:
        """
        Append a single message dict to a log file, creating it if needed.

        :param filepath: Absolute path to the JSON log file.
        :type filepath: str
        :param message: Message dict to append to the messages list.
        :type message: dict
        :return: None
        :rtype: None
        """
        messages = self.read_messages(filepath)
        messages.append(message)
        with open(filepath, "w", encoding="utf-8") as file_handle:
            json.dump({"messages": messages}, file_handle, ensure_ascii=False, indent=2)

    # Public write methods

    def save_broadcast_message(self, sender: str, text: str, timestamp: str) -> None:
        """
        Persist a broadcast message to broadcast.json.

        :param sender: Username of the message author.
        :type sender: str
        :param text: Message body.
        :type text: str
        :param timestamp: ISO-8601 timestamp string.
        :type timestamp: str
        :return: None
        :rtype: None
        """
        message = {
            "type": "MSG",
            "sender": sender,
            "target": "BROADCAST",
            "text": text,
            "timestamp": timestamp
        }
        self.append_message(self.broadcast_path, message)

    def save_dm_message(self, sender: str, target: str, text: str, timestamp: str) -> None:
        """
        Persist a direct message to the appropriate dm-<a>-<b>.json file.

        :param sender: Username of the message author.
        :type sender: str
        :param target: Username of the recipient.
        :type target: str
        :param text: Message body.
        :type text: str
        :param timestamp: ISO-8601 timestamp string.
        :type timestamp: str
        :return: None
        :rtype: None
        """
        message = {
            "type": "MSG",
            "sender": sender,
            "target": target,
            "text": text,
            "timestamp": timestamp
        }
        self.append_message(self.dm_path(sender, target), message)

    # Public read methods

    def load_broadcast_history(self) -> list:
        """
        Return all persisted broadcast messages, oldest first.

        :return: List of broadcast message dicts.
        :rtype: list
        """
        return self.read_messages(self.broadcast_path)

    def load_dm_history(self, username1: str, username2: str) -> list:
        """
        Return all persisted DM messages for the conversation between two users.

        :param username1: First participant username.
        :type username1: str
        :param username2: Second participant username.
        :type username2: str
        :return: List of DM message dicts for the conversation.
        :rtype: list
        """
        return self.read_messages(self.dm_path(username1, username2))

    def load_all_history_for_user(self, username: str) -> dict:
        """
        Build the complete chat history dict for a user who is logging in.

        Scans all DM files that involve the given username and groups the messages
        by conversation partner.

        :param username: The handle of the user who is logging in.
        :type username: str
        :return: Dict with key 'BROADCAST' (list) and one key per DM partner (list),
            e.g. {'BROADCAST': [...], 'Alice': [...], 'Charlie': [...]}.
        :rtype: dict
        """
        history = {"BROADCAST": self.load_broadcast_history()}

        # dm-<a>-<b>.json where a and b are separated by a single dash.
        # Since usernames only contain [a-zA-Z0-9_], splitting on '-' is unambiguous.
        for filepath in glob.glob(os.path.join(self._logs_dir, "dm-*.json")):
            filename = os.path.basename(filepath)
            # Strip "dm-" prefix and ".json" suffix, then split on first dash
            inner = filename[3:-5]
            parts = inner.split("-", 1)
            if len(parts) != 2:
                continue
            user_a, user_b = parts[0], parts[1]
            if user_a == username:
                history[user_b] = self.read_messages(filepath)
            elif user_b == username:
                history[user_a] = self.read_messages(filepath)

        return history
