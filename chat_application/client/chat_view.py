import tkinter as tk
from tkinter import ttk


class ChatView(tk.Frame):
    """Right-hand panel displaying the active chat with a header, message history, and input bar.

    Layout:
        3A  Header label   - shows active channel name.
        3B  Text widget    - scrollable, read-only message history with styled bubbles.
        3C  Input bar      - text entry + Send button, bound to the Enter key.

    Message rendering uses tk.Text tags to align and color messages:
        own_bubble     Right-indented, light-green background.
        other_bubble   Left-indented, light-gray background.
        system_msg     Centered, italic, muted gray - for SYS notifications.
        name_own       Bold green username label for own messages.
        name_other     Bold blue username label for others' messages.
        timestamp_tag  Small gray timestamp displayed next to the username.

    Callbacks:
        on_send_callback: Called with the stripped message text when the user sends.
    """

    BG_CHAT = "#ffffff"
    BG_OWN = "#DCF8C6"
    BG_OTHER = "#f0f0f0"
    COLOR_SYS = "#9e9e9e"
    COLOR_NAME_OWN = "#1b5e20"
    COLOR_NAME_OTHER = "#0d47a1"
    COLOR_TIMESTAMP = "#aaaaaa"

    def __init__(self, parent: tk.Widget, on_send_callback: callable):
        """Args:
            parent: Parent Tkinter widget.
            on_send_callback: Callback(text: str) invoked with message text on send.
        """
        super().__init__(parent, bg=self.BG_CHAT)
        self._on_send = on_send_callback
        self._own_username: str = None
        self.build_widgets()

    def build_widgets(self):
        """Construct header, chat history Text widget with scrollbar, and input bar."""
        # 3A Header
        self._header_label = tk.Label(
            self,
            text="📢 BROADCAST CHANNEL",
            bg="#1976D2",
            fg="white",
            font=("Arial", 11, "bold"),
            pady=8,
            anchor=tk.W,
            padx=12,
        )
        self._header_label.pack(fill=tk.X)

        # 3B Chat history
        history_frame = tk.Frame(self, bg=self.BG_CHAT)
        history_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._text_area = tk.Text(
            history_frame,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,
            bg=self.BG_CHAT,
            wrap=tk.WORD,
            padx=10,
            pady=6,
            relief=tk.FLAT,
            font=("Arial", 10),
            cursor="arrow",
        )
        self._text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._text_area.yview)

        self.configure_tags()

        # 3C Input bar
        input_frame = tk.Frame(self, bg="#f5f5f5", pady=6)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self._message_var = tk.StringVar()
        self._input_entry = tk.Entry(
            input_frame,
            textvariable=self._message_var,
            font=("Arial", 10),
            relief=tk.SOLID,
            bd=1,
        )
        self._input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 6), ipady=5)
        self._input_entry.bind("<Return>", self.on_enter_pressed)

        self._send_btn = tk.Button(
            input_frame,
            text="Send 🚀",
            command=self.on_send_clicked,
            bg="#1976D2",
            fg="white",
            activebackground="#0D47A1",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            font=("Arial", 10),
            cursor="hand2",
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def configure_tags(self):
        """Set up Text widget tags for message styling."""
        self._text_area.tag_configure(
            "name_own", font=("Arial", 9, "bold"), foreground=self.COLOR_NAME_OWN
        )
        self._text_area.tag_configure(
            "name_other", font=("Arial", 9, "bold"), foreground=self.COLOR_NAME_OTHER
        )
        self._text_area.tag_configure(
            "timestamp_tag", font=("Arial", 8), foreground=self.COLOR_TIMESTAMP
        )
        self._text_area.tag_configure(
            "own_bubble",
            background=self.BG_OWN,
            lmargin1=100,
            lmargin2=100,
            rmargin=10,
            spacing3=4,
        )
        self._text_area.tag_configure(
            "other_bubble",
            background=self.BG_OTHER,
            lmargin1=10,
            lmargin2=10,
            rmargin=100,
            spacing3=4,
        )
        self._text_area.tag_configure(
            "system_msg",
            foreground=self.COLOR_SYS,
            font=("Arial", 9, "italic"),
            justify=tk.CENTER,
            spacing1=4,
            spacing3=4,
        )

    # Event handlers

    def on_enter_pressed(self, _event):
        self.on_send_clicked()

    def on_send_clicked(self):
        text = self._message_var.get().strip()
        if text:
            self._on_send(text)
            self._message_var.set("")

    # Properties

    @property
    def header(self) -> str:
        """The text currently shown in the channel/DM header label."""
        return self._header_label.cget("text")

    @header.setter
    def header(self, title: str):
        """Update the channel/DM header label.

        Args:
            title: New header text (e.g., '📢 BROADCAST CHANNEL' or '💬 Private Chat with @Bob').
        """
        self._header_label.config(text=title)

    @property
    def own_username(self) -> str:
        """The local user's handle used for message alignment."""
        return self._own_username

    @own_username.setter
    def own_username(self, username: str):
        """Set the local user's username for message alignment.

        Args:
            username: The authenticated username of the local user.
        """
        self._own_username = username

    @property
    def input_enabled(self) -> bool:
        """True when the input entry and send button are active."""
        return self._input_entry["state"] == str(tk.NORMAL)

    @input_enabled.setter
    def input_enabled(self, enabled: bool):
        """Enable or disable the message input entry and send button.

        Args:
            enabled: True to allow sending, False to disable (e.g., when offline).
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self._input_entry.config(state=state)
        self._send_btn.config(state=state)

    # Public methods

    def add_message(self, sender: str, text: str, timestamp: str, is_system: bool = False):
        """Append a single message entry to the history area.

        Args:
            sender: Username of the message author.
            text: Message body.
            timestamp: ISO-8601 timestamp string.
            is_system: True for SYS-type notifications (centered, italic style).
        """
        self._text_area.config(state=tk.NORMAL)

        if is_system:
            self._text_area.insert(tk.END, f"\n  {text}\n", "system_msg")
        elif sender == self._own_username:
            self._text_area.insert(tk.END, "\n")
            self._text_area.insert(tk.END, f"[{sender}] ", "name_own")
            self._text_area.insert(tk.END, f"{timestamp}\n", "timestamp_tag")
            self._text_area.insert(tk.END, f"{text}\n", "own_bubble")
        else:
            self._text_area.insert(tk.END, "\n")
            self._text_area.insert(tk.END, f"[{sender}] ", "name_other")
            self._text_area.insert(tk.END, f"{timestamp}\n", "timestamp_tag")
            self._text_area.insert(tk.END, f"{text}\n", "other_bubble")

        self._text_area.config(state=tk.DISABLED)
        self._text_area.see(tk.END)

    def clear(self):
        """Remove all messages from the history display."""
        self._text_area.config(state=tk.NORMAL)
        self._text_area.delete("1.0", tk.END)
        self._text_area.config(state=tk.DISABLED)

    def load_history(self, messages: list):
        """Clear the view and render a list of stored message dicts.

        Args:
            messages: List of message payload dicts (MSG or SYS type).
        """
        self.clear()
        for msg in messages:
            if msg.get("type") == "SYS":
                self.add_message("SYSTEM", msg.get("text", ""), msg.get("timestamp", ""), is_system=True)
            else:
                self.add_message(
                    msg.get("sender", ""),
                    msg.get("text", ""),
                    msg.get("timestamp", ""),
                )
