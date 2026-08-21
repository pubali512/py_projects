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

    BG_COLOR = "#f5f5f5"
    CONNECT_COLOR = "#4CAF50"
    DISCONNECT_COLOR = "#e53935"

    def __init__(self, parent: tk.Widget, on_connect: callable, on_disconnect: callable):
        """Args:
            parent: Parent Tkinter widget.
            on_connect: Zero-argument callback for the Connect button.
            on_disconnect: Zero-argument callback for the Disconnect button.
        """
        super().__init__(parent, bg=self.BG_COLOR, pady=6)
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._status_text = tk.StringVar(value="Status: Offline")
        self.build_widgets()

    def build_widgets(self):
        """Construct and lay out all child widgets."""
        self._connect_btn = tk.Button(
            self,
            text="Connect 🟢",
            command=self._on_connect,
            bg=self.CONNECT_COLOR,
            fg="white",
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
            fg="white",
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

    def set_online(self, username: str):
        """Switch the bar to online state and display the active username.

        Args:
            username: The authenticated handle shown in the status label.
        """
        self._status_text.set(f"Status: Online as @{username}")
        self._connect_btn.config(state=tk.DISABLED)
        self._disconnect_btn.config(state=tk.NORMAL)

    def set_offline(self):
        """Switch the bar to offline state and reset all controls."""
        self._status_text.set("Status: Offline")
        self._connect_btn.config(state=tk.NORMAL)
        self._disconnect_btn.config(state=tk.DISABLED)
