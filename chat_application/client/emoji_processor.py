class EmojiProcessor:
    """Replaces text shortcodes with their Unicode emoji equivalents.

    Shortcodes are replaced left-to-right in a single pass, so longer or more
    specific patterns should appear first in SHORTCODE_MAP to avoid partial matches.

    Supported shortcodes:
        :fire:   -> 🔥
        :like:   -> 👍
        :check:  -> ✅
        :)       -> 😊
        :(       -> 😢
        <3       -> ❤️
    """

    SHORTCODE_MAP: list[tuple[str, str]] = [
        (":fire:", "🔥"),
        (":like:", "👍"),
        (":check:", "✅"),
        (":)", "😊"),
        (":(", "😢"),
        ("<3", "❤️"),
    ]

    @staticmethod
    def process(text: str) -> str:
        """Replace all recognized shortcodes in text with their emoji characters.

        Args:
            text: Raw message text typed by the user.

        Returns:
            Text with all shortcodes substituted. Unknown tokens are unchanged.
        """
        for shortcode, emoji in EmojiProcessor.SHORTCODE_MAP:
            text = text.replace(shortcode, emoji)
        return text
