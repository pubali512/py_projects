# Teams Lite Chat Application

## Overview & Program Functionality

Teams Lite Chat is a desktop Python chat application that allows multiple users to communicate in real time over a shared server. It provides a clean Tkinter graphical interface with a public broadcast channel and private direct messaging, along with persistent chat history that reloads automatically on login.

### What the Program Does

- **Real-time messaging** — Messages are delivered instantly to all connected users (broadcast) or privately to one recipient (DM).
- **Broadcast channel** — A public channel where all connected users can post and read at the same time.
- **Direct messages** — Clicking a username in the sidebar opens a private 1-on-1 conversation tab.
- **Chat history reload** — On login, the server sends the full broadcast history and all private conversation histories back to the client automatically.
- **Live presence list** — The sidebar updates in real time as users join and leave. Unread messages are highlighted in bold until the conversation is opened.
- **Emoji shortcodes** — Typing `:)`, `:(`, `<3`, `:fire:`, `:like:`, or `:check:` replaces them with the corresponding Unicode emoji before sending.

### Reusability & Object-Oriented Design

The project is built with modularity and clean OOP principles throughout:

- **Separation of concerns** — The server and client are fully decoupled. The server has no GUI dependency; the client has no file-system dependency.
- **Inheritance for GUI components** — `ControlBar`, `SidebarPanel`, and `ChatView` all subclass `tk.Frame`, reusing Tkinter's widget lifecycle while each encapsulates its own layout and state.
- **Single-responsibility classes** — Each class does exactly one thing: `MessageRouter` routes messages, `ChatLogger` persists logs, `EmojiProcessor` transforms text, and `UsernameValidator` validates names.
- **Shared validation logic** — `UsernameValidator` is imported by both the client (pre-send check) and the server (handshake), enforcing the same username rules on both sides with no code duplication.
- **Callback-based decoupling** — `ChatClient` and `NetworkReceiver` receive their event handlers as constructor parameters, keeping them independent of the GUI and easy to test in isolation.
- **Standard library only** — Built entirely on Python's built-in modules (`tkinter`, `socket`, `threading`, `json`, `glob`, `datetime`, `os`, `sys`) with no external dependencies.

---

## Required Packages

- **Python 3.10+** — uses PEP 585 generic type hints (e.g., `tuple[bool, str]`)

No third-party packages are required. All functionality relies on standard library modules:

| Module | Purpose |
|--------|---------|
| `tkinter` | Desktop GUI |
| `socket` | TCP networking |
| `threading` | Background receive thread |
| `json` | Protocol encoding and chat log persistence |
| `glob` | Scanning DM log files on login |
| `datetime` | Server-side message timestamps |
| `os`, `sys` | Path handling and import configuration |

---

## Usage

### 1. Start the Server

Open a terminal in the `chat_application/` directory and run:

```bash
python server/server_main.py
```

The server prints `Server listening on localhost:5555` when ready. Leave this terminal open.

### 2. Launch One or More Clients

Open a separate terminal for each user:

```bash
python client/client_main.py
```

**Connecting:**
1. Click **Connect 🟢**.
2. Enter a username (letters, digits, and underscores only; 1 to 20 characters).
3. Click OK. The status bar shows `Online as @<username>` on success.

**Chatting:**
- Type a message in the input bar and press **Enter** or click **Send 🚀**.
- Messages go to whichever conversation is currently selected in the sidebar.
- Click **📢 BROADCAST** to post to the public channel.
- Click any username in the sidebar to open a private chat.

**Disconnecting:**
- Click **Disconnect 🔴** to leave gracefully. All messages you sent are still saved on the server.

---

## Project Structure

```
chat_application/
    config.json               Shared host and port configuration
    common/
        protocol.py           Protocol class: message types, encode/decode helpers
        username_validator.py UsernameValidator class: username validation
    server/
        server_main.py        Entry point — reads config and starts ChatServer
        chat_server.py        ChatServer: accepts TCP connections, spawns handler threads
        client_handler.py     ClientHandler: per-client socket read loop
        message_router.py     MessageRouter: routes broadcast and DM messages
        user_registry.py      UserRegistry: maps online usernames to send callbacks
        chat_logger.py        ChatLogger: reads and writes JSON chat log files
        chat_logs/            Auto-created directory for log files
    client/
        client_main.py        Entry point — reads config and launches AppGui
        app_gui.py            AppGui: main window and component orchestrator
        control_bar.py        ControlBar: top connect/disconnect toolbar
        sidebar_panel.py      SidebarPanel: broadcast button and online user list
        chat_view.py          ChatView: channel header, scrollable history, input bar
        chat_client.py        ChatClient: manages the TCP socket connection
        network_receiver.py   NetworkReceiver: background thread for incoming messages
        emoji_processor.py    EmojiProcessor: shortcode-to-emoji substitution
    docs/
        user_documentation.md This file
        README.md             Developer reference
        flowchart.drawio      Server and client execution flow diagrams
        architecture.drawio   High-level class architecture diagram
        chat_application_fs.drawio  Module structure with public APIs
```

---

## Configuration

Edit `config.json` to change the host or port. Both the server and every client read this file at startup:

```json
{
  "host": "localhost",
  "port": 5555
}
```

---

## Username Rules

| Rule | Detail |
|------|--------|
| Allowed characters | Letters (`A–Z`, `a–z`), digits (`0–9`), underscore (`_`) |
| Length | 1 to 20 characters |
| Reserved handles | `BROADCAST`, `SYSTEM` |
| Uniqueness | Must not match any currently connected username |

---

## Emoji Shortcodes

Type any of the following and they will be replaced before the message is sent:

| Shortcode | Result |
|-----------|--------|
| `:)` | 😊 |
| `:(` | 😢 |
| `<3` | ❤️ |
| `:fire:` | 🔥 |
| `:like:` | 👍 |
| `:check:` | ✅ |
