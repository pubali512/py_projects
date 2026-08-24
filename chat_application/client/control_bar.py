import tkinter as tk


class ControlBar(tk.Frame):
    """Top control bar containing Connect/Disconnect buttons and a status label.

    Callbacks:
        on_connect:    Called when the user clicks the Connect button.
        on_disconnect: Called when the user clicks the Disconnect button.

    State transitions:
        set_online(username)  -> disables Connect, enables Disconnect, updates label.
        set_offline()         -> enables Connect, disables Disconnect, resets label.
    """

    DISABLED_FG_COLOR = "#968B8B"
    BG_COLOR = "#f5f5f5"
    CONNECT_COLOR = "#88D18A"
    DISCONNECT_COLOR = "#f08381"

    def __init__(self, parent: tk.Widget, on_connect: callable, on_disconnect: callable) -> None:
        """
        :param parent: Parent Tkinter widget.
        :type parent: tk.Widget
        :param on_connect: Called when the Connect button is clicked.
        :type on_connect: callable
        :param on_disconnect: Called when the Disconnect button is clicked.
        :type on_disconnect: callable
        :return: None
        :rtype: None
        """
        super().__init__(parent, bg=self.BG_COLOR, pady=6)
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._status_text = tk.StringVar(value="Status: Offline")
        self._build_ui()

    def _build_ui(self) -> None:
        """
        Build and arrange the Connect, Disconnect, and status widgets.

        :return: None
        :rtype: None
        """
        self._connect_btn = tk.Button(
            self,
            text="Connect 🟢",
            command=self._on_connect,
            bg=self.CONNECT_COLOR,
            fg="black",
            disabledforeground=self.DISABLED_FG_COLOR,
            activebackground="#388E3C",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
        )
        self._connect_btn.pack(side=tk.LEFT, padx=(10, 5))

        self._disconnect_btn = tk.Button(
            self,
            text="Disconnect 🔴",
            command=self._on_disconnect,
            bg=self.DISCONNECT_COLOR,
            fg="black",
            disabledforeground=self.DISABLED_FG_COLOR,
            activebackground="#b71c1c",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            state=tk.DISABLED,
            cursor="hand2",
        )
        self._disconnect_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(
            self,
            textvariable=self._status_text,
            bg=self.BG_COLOR,
            fg="#444444",
            font=("Arial", 10),
        ).pack(side=tk.RIGHT, padx=15)

    def set_online(self, username: str) -> None:
        """
        Switch to online state and show the active username.

        :param username: The authenticated username to display.
        :type username: str
        :return: None
        :rtype: None
        """
        self._status_text.set(f"Status: Online as @{username}")
        self._connect_btn.config(state=tk.DISABLED)
        self._disconnect_btn.config(state=tk.NORMAL)

    def set_offline(self) -> None:
        """
        Switch to offline state and reset all controls.

        :return: None
        :rtype: None
        """
        self._status_text.set("Status: Offline")
        self._connect_btn.config(state=tk.NORMAL)
        self._disconnect_btn.config(state=tk.DISABLED)
