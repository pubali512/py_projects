import re


class UsernameValidator:
    """Validates chat usernames against the application naming rules.

    Rules enforced:
        - Only uppercase letters, lowercase letters, digits, and underscores.
        - Length between 1 and 20 characters inclusive.
        - The reserved handles BROADCAST and SYSTEM are rejected.
        - Applied by both the client (pre-send check) and the server (handshake).
    """

    PATTERN = re.compile(r"^[a-zA-Z0-9_]{1,20}$")
    RESERVED = frozenset({"BROADCAST", "SYSTEM"})
    MIN_LENGTH = 1
    MAX_LENGTH = 20

    @staticmethod
    def validate(username: str) -> tuple[bool, str]:
        """
        Check if a username follows all naming rules.

        :param username: The username to check.
        :type username: str
        :return: Tuple (is_valid, reason). reason is empty if the username is valid.
        :rtype: tuple[bool, str]
        """
        if not username or len(username) < UsernameValidator.MIN_LENGTH:
            return False, "Username must be at least 1 character long"
        if len(username) > UsernameValidator.MAX_LENGTH:
            return False, f"Username must be at most {UsernameValidator.MAX_LENGTH} characters long"
        if username in UsernameValidator.RESERVED:
            return False, f"'{username}' is a reserved handle and cannot be used"
        if not UsernameValidator.PATTERN.match(username):
            return False, "Username may only contain letters, digits, and underscores"
        return True, ""
