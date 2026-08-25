class EmojiProcessor:
    """Replaces text shortcodes with their Unicode emoji equivalents.

    Shortcodes are replaced left-to-right in a single pass, so longer or more
    specific patterns should appear first in SHORTCODE_MAP to avoid partial matches.

    Supported shortcodes:
        :birthday: -> 🎂
        :haha:     -> 🤣
        :lol:      -> 😂
        :fire:     -> 🔥
        :like:     -> 👍
        :check:    -> ✅
        :)         -> 😊
        :(         -> 😢
        <3         -> ❤️
    """

    SHORTCODE_MAP: list[tuple[str, str]] = [
        (":birthday:", "🎂"),
        (":haha:", "🤣"),
        (":lol:", "😂"),
        (":fire:", "🔥"),
        (":like:", "👍"),
        (":check:", "✅"),
        (":)", "😊"),
        (":(", "😢"),
        ("<3", "❤️"),
    ]

    @staticmethod
    def process(text: str) -> str:
        """
        Replace emoji shortcodes in text with their Unicode characters.

        :param text: Raw message text from the user.
        :type text: str
        :return: Text with shortcodes substituted. Unknown tokens are left unchanged.
        :rtype: str
        """
        for shortcode, emoji in EmojiProcessor.SHORTCODE_MAP:
            text = text.replace(shortcode, emoji)
        return text
