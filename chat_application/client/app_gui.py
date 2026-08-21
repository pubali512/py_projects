import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from client.chat_client import ChatClient
from client.chat_view import ChatView
from client.control_bar import ControlBar
from client.emoji_processor import EmojiProcessor
from client.sidebar_panel import SidebarPanel
from common.protocol import Protocol
from common.username_validator import UsernameValidator


class AppGui:
    """Main application window. Orchestrates all GUI components and network logic.

    Responsibilities:
        - Create and lay out ControlBar, SidebarPanel, and ChatView.
        - Instantiate ChatClient on connect and tear it down on disconnect.
        - Maintain the in-memory chat history store for all conversations.
        - Dispatch incoming network messages to the appropriate GUI action via
          root.after() to ensure all widget updates happen on the main thread.
        - Route user actions (send, switch chat, connect/disconnect) to the
          correct component or network method.

    History store:
        self._history is a dict[str, list[dict]] mapping a conversation key to an
        ordered list of message payload dicts.
        Key 'BROADCAST' holds the public channel. Any other key is a DM partner username.
    """

    WINDOW_TITLE = "Teams Lite Chat"
    WINDOW_MIN_WIDTH = 700
    WINDOW_MIN_HEIGHT = 450
    WINDOW_START_SIZE = "960x600"

    def __init__(self, config: dict):
        """Args:
            config: Dict with 'host' (str) and 'port' (int) keys read from config.json.
        """
        self._config = config
        self._chat_client: ChatClient = None
        self._my_username: str = None
        self._active_target: str = Protocol.TARGET_BROADCAST
        self._history: dict[str, list] = {Protocol.TARGET_BROADCAST: []}

        self._root = tk.Tk()
        self._root.title(self.WINDOW_TITLE)
        self._root.geometry(self.WINDOW_START_SIZE)
        self._root.minsize(self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT)

        self.build_layout()

    def build_layout(self):
        """Create and arrange top bar, sidebar, divider, and chat view."""
        self._control_bar = ControlBar(
            self._root,
            on_connect=self.on_connect_clicked,
            on_disconnect=self.on_disconnect_clicked,
        )
        self._control_bar.pack(fill=tk.X, side=tk.TOP)

        ttk.Separator(self._root, orient=tk.HORIZONTAL).pack(fill=tk.X)

        main_frame = tk.Frame(self._root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._sidebar = SidebarPanel(
            main_frame,
            on_broadcast_click=lambda: self.switch_chat(Protocol.TARGET_BROADCAST),
            on_user_click=self.switch_chat,
        )
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Separator(main_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y)

        self._chat_view = ChatView(main_frame, on_send_callback=self.on_send_message)
        self._chat_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._chat_view.input_enabled = False

    # Connect / disconnect

    def on_connect_clicked(self):
        """Prompt for a username, validate locally, then attempt server connection."""
        username = simpledialog.askstring("Connect", "Enter your username:", parent=self._root)
        if not username:
            return

        is_valid, reason = UsernameValidator.validate(username)
        if not is_valid:
            messagebox.showerror("Invalid Username", reason, parent=self._root)
            return

        host = self._config.get("host", "localhost")
        port = self._config.get("port", 5555)

        self._chat_client = ChatClient(
            host=host,
            port=port,
            on_message=self.dispatch_incoming_message,
            on_disconnect=self.on_network_disconnect,
        )

        success, error = self._chat_client.connect(username)
        if not success:
            messagebox.showerror("Connection Failed", error, parent=self._root)
            self._chat_client = None

    def on_disconnect_clicked(self):
        """Gracefully disconnect from the server."""
        if self._chat_client:
            self._chat_client.disconnect()

    def on_network_disconnect(self):
        """Called from the network thread when the connection drops; dispatches to GUI thread."""
        self._root.after(0, self.reset_to_offline)

    def reset_to_offline(self):
        """Reset all GUI components to the offline/disconnected state."""
        self._my_username = None
        self._active_target = Protocol.TARGET_BROADCAST
        self._history = {Protocol.TARGET_BROADCAST: []}
        self._chat_client = None
        self._control_bar.set_offline()
        self._sidebar.set_users([])
        self._sidebar.active_target = None
        self._chat_view.header = "📢 BROADCAST CHANNEL"
        self._chat_view.clear()
        self._chat_view.input_enabled = False

    # Incoming message dispatch

    def dispatch_incoming_message(self, payload: dict):
        """Schedule GUI update for an incoming server message on the main thread."""
        self._root.after(0, self.handle_incoming_message, payload)

    def handle_incoming_message(self, payload: dict):
        """Route a server message payload to the appropriate handler."""
        msg_type = payload.get("type")
        handlers = {
            Protocol.TYPE_LOGIN_OK: self.on_login_ok,
            Protocol.TYPE_LOGIN_ERR: self.on_login_err,
            Protocol.TYPE_MSG: self.on_msg_received,
            Protocol.TYPE_USERS: self.on_users_update,
            Protocol.TYPE_SYS: self.on_sys_message,
        }
        handler = handlers.get(msg_type)
        if handler:
            handler(payload)

    # Specific message handlers

    def on_login_ok(self, payload: dict):
        """Initialize the session after the server approves the login."""
        users = payload.get("users", [])
        server_history = payload.get("history", {})

        self._my_username = self._chat_client.username
        self._chat_view.own_username = self._my_username
        self._control_bar.set_online(self._my_username)

        self._history = {Protocol.TARGET_BROADCAST: server_history.get(Protocol.TARGET_BROADCAST, [])}
        for partner, messages in server_history.items():
            if partner != Protocol.TARGET_BROADCAST:
                self._history[partner] = messages

        peer_list = [u for u in users if u != self._my_username]
        self._sidebar.set_users(peer_list)
        self._chat_view.input_enabled = True
        self.switch_chat(Protocol.TARGET_BROADCAST)

    def on_login_err(self, payload: dict):
        """Show an error dialog when the server rejects the login and clean up."""
        reason = payload.get("reason", "Login rejected by server")
        messagebox.showerror("Login Failed", reason, parent=self._root)
        if self._chat_client:
            self._chat_client.disconnect()
        self._chat_client = None

    def on_msg_received(self, payload: dict):
        """Store an incoming MSG and render it or highlight the sidebar entry."""
        target = payload.get("target", "")
        sender = payload.get("sender", "")
        text = payload.get("text", "")
        timestamp = payload.get("timestamp", "")

        if target == Protocol.TARGET_BROADCAST:
            conv_key = Protocol.TARGET_BROADCAST
        elif sender == self._my_username:
            conv_key = target
        else:
            conv_key = sender

        if conv_key not in self._history:
            self._history[conv_key] = []
        self._history[conv_key].append(payload)

        if conv_key == self._active_target:
            self._chat_view.add_message(sender, text, timestamp)
        elif conv_key != Protocol.TARGET_BROADCAST:
            self._sidebar.highlight_user(conv_key)

    def on_users_update(self, payload: dict):
        """Refresh the sidebar user list when the server sends a USERS message."""
        users = payload.get("users", [])
        peer_list = [u for u in users if u != self._my_username]
        self._sidebar.set_users(peer_list)
        if self._active_target != Protocol.TARGET_BROADCAST:
            self._sidebar.active_target = self._active_target

    def on_sys_message(self, payload: dict):
        """Display a system notification in the broadcast channel history."""
        text = payload.get("text", "")
        timestamp = payload.get("timestamp", "")
        sys_entry = {"type": "SYS", "text": text, "timestamp": timestamp}
        self._history[Protocol.TARGET_BROADCAST].append(sys_entry)

        if self._active_target == Protocol.TARGET_BROADCAST:
            self._chat_view.add_message("SYSTEM", text, timestamp, is_system=True)

    # Send message

    def on_send_message(self, text: str):
        """Process emoji shortcodes and send the message to the active target."""
        if not self._chat_client or not self._chat_client.is_connected:
            return
        processed_text = EmojiProcessor.process(text)
        self._chat_client.send_message(self._active_target, processed_text)

    # Chat target switching

    def switch_chat(self, target: str):
        """Switch the main chat view to the given channel or DM target.

        Args:
            target: 'BROADCAST' for the public channel, or a username for a DM.
        """
        self._active_target = target

        if target == Protocol.TARGET_BROADCAST:
            self._chat_view.header = "📢 BROADCAST CHANNEL"
            self._sidebar.active_target = None
        else:
            self._chat_view.header = f"💬 Private Chat with @{target}"
            self._sidebar.clear_highlight(target)
            self._sidebar.active_target = target

        messages = self._history.get(target, [])
        self._chat_view.load_history(messages)

    # Main loop

    def run(self):
        """Enter the Tkinter event loop. Blocks until the window is closed."""
        self._root.mainloop()
