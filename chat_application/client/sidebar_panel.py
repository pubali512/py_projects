import tkinter as tk


class SidebarPanel(tk.Frame):
    """Left sidebar panel with a Broadcast button and the scrollable online user list.

    Layout:
        [📢 BROADCAST] button (fixed at top)
        ONLINE MEMBERS label
        Dynamically populated list of user buttons (one per connected peer)

    Highlighting:
        When a new message arrives from a user who is not the current active chat,
        highlight_user() makes that user's button bold. Clicking the button (which
        triggers on_user_click) should be paired with clear_highlight() by the caller.

    Callbacks:
        on_broadcast_click: Called with no arguments when the Broadcast button is clicked.
        on_user_click:      Called with the username string when a user button is clicked.
    """

    BG_COLOR = "#eeeeee"
    ACTIVE_BG = "#b0c4de"
    INACTIVE_BG = "#eeeeee"
    FONT_NORMAL = ("Arial", 10)
    FONT_UNREAD = ("Arial", 10, "bold")

    def __init__(self, parent: tk.Widget, on_broadcast_click: callable, on_user_click: callable) -> None:
        """
        :param parent: Parent Tkinter widget.
        :type parent: tk.Widget
        :param on_broadcast_click: Called when the Broadcast button is clicked.
        :type on_broadcast_click: callable
        :param on_user_click: Called with a username when a user button is clicked.
        :type on_user_click: callable
        :return: None
        :rtype: None
        """
        super().__init__(parent, bg=self.BG_COLOR, width=190)
        self.pack_propagate(False)
        self._on_broadcast_click = on_broadcast_click
        self._on_user_click = on_user_click
        self._user_buttons: dict[str, tk.Button] = {}
        self._unread_users: set[str] = set()
        self._active_target: str = None
        self._build_ui()

    def _build_ui(self) -> None:
        """
        Build the broadcast button, section header, and user list container.

        :return: None
        :rtype: None
        """
        self._broadcast_btn = tk.Button(
            self,
            text="📢 BROADCAST",
            command=self._on_broadcast_click,
            bg="#1976D2",
            fg="white",
            activebackground="#0D47A1",
            relief=tk.FLAT,
            pady=9,
            font=("Arial", 10, "bold"),
            cursor="hand2",
        )
        self._broadcast_btn.pack(fill=tk.X, padx=8, pady=(8, 4))

        tk.Label(
            self,
            text="ONLINE MEMBERS",
            bg=self.BG_COLOR,
            fg="#757575",
            font=("Arial", 8, "bold"),
        ).pack(anchor=tk.W, padx=10, pady=(6, 2))

        self._user_list_frame = tk.Frame(self, bg=self.BG_COLOR)
        self._user_list_frame.pack(fill=tk.BOTH, expand=True, padx=6)

    def set_users(self, usernames: list[str]) -> None:
        """
        Rebuild the user list from the given usernames.

        Existing unread highlights are preserved for users still online.
        Users who left are removed from the unread set.

        :param usernames: Online peer usernames (own username excluded).
        :type usernames: list[str]
        :return: None
        :rtype: None
        """
        for widget in self._user_list_frame.winfo_children():
            widget.destroy()
        self._user_buttons.clear()
        self._unread_users &= set(usernames)

        for username in usernames:
            font = self.FONT_UNREAD if username in self._unread_users else self.FONT_NORMAL
            bg = self.ACTIVE_BG if username == self._active_target else self.INACTIVE_BG

            btn = tk.Button(
                self._user_list_frame,
                text=f"🟢 {username}",
                command=lambda u=username: self._on_user_click(u),
                bg=bg,
                activebackground=self.ACTIVE_BG,
                relief=tk.FLAT,
                anchor=tk.W,
                padx=8,
                pady=3,
                font=font,
                cursor="hand2",
            )
            btn.pack(fill=tk.X, pady=1)
            self._user_buttons[username] = btn

    def highlight_user(self, username: str) -> None:
        """
        Mark a user as having an unread message (bold text).

        :param username: The user with the new message.
        :type username: str
        :return: None
        :rtype: None
        """
        self._unread_users.add(username)
        btn = self._user_buttons.get(username)
        if btn:
            btn.config(font=self.FONT_UNREAD)

    def clear_highlight(self, username: str) -> None:
        """
        Remove the unread indicator from a user's button.

        :param username: The user whose highlight to clear.
        :type username: str
        :return: None
        :rtype: None
        """
        self._unread_users.discard(username)
        btn = self._user_buttons.get(username)
        if btn:
            btn.config(font=self.FONT_NORMAL)

    @property
    def active_target(self) -> str:
        """
        The selected DM peer username, or None if Broadcast is active.
        """
        return self._active_target

    @active_target.setter
    def active_target(self, target: str) -> None:
        """
        Update the visual highlight to show the selected chat target.

        :param target: Username of the active DM peer, or None for Broadcast.
        :type target: str
        :return: None
        :rtype: None
        """
        self._active_target = target
        for username, btn in self._user_buttons.items():
            btn.config(bg=self.ACTIVE_BG if username == target else self.INACTIVE_BG)
