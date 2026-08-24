import tkinter as tk
from tkinter import ttk


class ChatView(tk.Frame):
    """Right-hand panel displaying the active chat with a header, message history, and input bar.

    Layout:
        (TOP)    Header label   - shows active channel name.
        (MID)    History frame  - scrollable message history (own and others' messages are shown in different styles).
        (BOTTOM) Input bar      - text entry + Send button (also bound to the Enter key).

    tk.Text tags are used to align and color messages:
        own_bubble     Light-gray background.
        other_bubble   Light-green background.
        system_msg     Centered, italic, muted gray - for SYS notifications.
        name_own       Bold green username label for own messages.
        name_other     Bold blue username label for others' messages.
        timestamp_tag  Small gray timestamp displayed next to the username.

    Callbacks:
        on_send_callback: Called with the stripped message text when the user sends.
    """

    BG_CHAT = "#ffffff"
    BG_OWN = "#f0f0f0"
    BG_OTHER = "#DCF8C6"
    COLOR_SYS = "#9e9e9e"
    COLOR_NAME_OWN = "#1b5e20"
    COLOR_NAME_OTHER = "#0d47a1"
    COLOR_TIMESTAMP = "#aaaaaa"

    def __init__(self, parent: tk.Widget, on_send_callback: callable) -> None:
        """
        :param parent: Parent Tkinter widget.
        :type parent: tk.Widget
        :param on_send_callback: Called with the message text when the user sends.
        :type on_send_callback: callable
        :return: None
        :rtype: None
        """
        super().__init__(parent, bg=self.BG_CHAT)
        self._on_send = on_send_callback
        self._own_username: str = None
        self._build_ui()

    def _build_ui(self) -> None:
        """
        This method builds the header, message area, and input bar.

        :return: None
        :rtype: None
        """
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
            font=("Arial", 12),
            cursor="arrow",
        )
        self._text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._text_area.yview)

        self._configure_tags()

        # 3C Input bar
        input_frame = tk.Frame(self, bg="#f5f5f5", pady=6)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self._message_var = tk.StringVar()
        self._input_entry = tk.Entry(
            input_frame,
            textvariable=self._message_var,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
        )
        self._input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 6), ipady=5)
        self._input_entry.bind("<Return>", self._on_enter_pressed)

        self._send_btn = tk.Button(
            input_frame,
            text="Send 🚀",
            command=self._on_send_clicked,
            bg="#8DAFD2",
            fg="black",
            activebackground="#0D47A1",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            font=("Arial", 12),
            cursor="hand2",
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def _configure_tags(self) -> None:
        """
        This method sets up the styling tags for messages from different users.

        :return: None
        :rtype: None
        """
        self._text_area.tag_configure(
            "name_own", font=("Arial", 11, "bold"), foreground=self.COLOR_NAME_OWN
        )
        self._text_area.tag_configure(
            "name_other", font=("Arial", 11, "bold"), foreground=self.COLOR_NAME_OTHER
        )
        self._text_area.tag_configure(
            "timestamp_tag", font=("Arial", 11), foreground=self.COLOR_TIMESTAMP
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
            lmargin1=100,
            lmargin2=100,
            rmargin=10,
            spacing3=4,
        )
        self._text_area.tag_configure(
            "system_msg",
            foreground=self.COLOR_SYS,
            font=("Arial", 11, "italic"),
            justify=tk.CENTER,
            spacing1=4,
            spacing3=4,
        )

    # Event handlers

    def _on_enter_pressed(self, _event) -> None:
        self._on_send_clicked()

    def _on_send_clicked(self) -> None:
        text = self._message_var.get().strip()
        if text:
            self._on_send(text)
            self._message_var.set("")

    # Properties

    @property
    def header(self) -> str:
        """
        The text shown in the channel header label.
        """
        return self._header_label.cget("text")

    @header.setter
    def header(self, title: str) -> None:
        """
        This method updates the channel header text.

        :param title: New header text.
        :type title: str
        :return: None
        :rtype: None
        """
        self._header_label.config(text=title)

    @property
    def own_username(self) -> str:
        """
        The local user's handle used to align messages.
        """
        return self._own_username

    @own_username.setter
    def own_username(self, username: str) -> None:
        """
        This method sets the local user's username for message alignment.

        :param username: The authenticated username of the local user.
        :type username: str
        :return: None
        :rtype: None
        """
        self._own_username = username

    @property
    def input_enabled(self) -> bool:
        """
        True when the input entry and send button are active.
        """
        return self._input_entry["state"] == str(tk.NORMAL)

    @input_enabled.setter
    def input_enabled(self, enabled: bool) -> None:
        """
        This method enables or disables the message input and send button.

        :param enabled: True to allow sending, False to disable.
        :type enabled: bool
        :return: None
        :rtype: None
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self._input_entry.config(state=state)
        self._send_btn.config(state=state)

    # Public methods

    def add_message(self, sender: str, text: str, timestamp: str, is_system: bool = False) -> None:
        """
        This method appends a single message to the chat history area.

        :param sender: Username of the message author.
        :type sender: str
        :param text: Message text.
        :type text: str
        :param timestamp: ISO-8601 timestamp.
        :type timestamp: str
        :param is_system: True for system notifications (centered italic style).
        :type is_system: bool
        :return: None
        :rtype: None
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

    def clear(self) -> None:
        """
        This method clears all messages from the history display.

        :return: None
        :rtype: None
        """
        self._text_area.config(state=tk.NORMAL)
        self._text_area.delete("1.0", tk.END)
        self._text_area.config(state=tk.DISABLED)

    def load_history(self, messages: list) -> None:
        """
        This method clears the view and shows the given list of messages.

        :param messages: Message payload dicts to show (MSG or SYS type).
        :type messages: list
        :return: None
        :rtype: None
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
