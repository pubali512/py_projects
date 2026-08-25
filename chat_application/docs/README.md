# Teams Lite Chat Application

A desktop Python chat application demonstrating OOP design patterns, modular architecture, robust exception handling, and a Tkinter GUI.

## Features

- **Broadcast Channel** - public messages delivered to all connected users simultaneously
- **Direct Messaging (DM)** - click any online user to open a private 1-on-1 chat tab
- **Chat History Reload** - broadcast and DM history is automatically restored on login
- **Presence Indicators** - sidebar shows who is online in real time; users appear/disappear as they connect/disconnect
- **Unread Highlighting** - sidebar entry turns bold when a new message arrives from an inactive conversation
- **Emoji Shortcodes** - `:)` `:(` `<3` `:fire:` `:like:` `:check:` are replaced with Unicode emoji before sending

---

## Project Structure

```
chat_application/
    config.json               Server host and port configuration (shared)
    common/
        protocol.py           Protocol class: message types, encode/decode helpers
        username_validator.py UsernameValidator class: naming-rule enforcement
    server/
        server_main.py        Entry point - reads config and starts ChatServer
        chat_server.py        ChatServer: accepts TCP connections, spawns threads
        client_handler.py     ClientHandler: per-client message loop (one thread each)
        message_router.py     MessageRouter: routes broadcast and DM messages
        user_registry.py      UserRegistry: thread-safe active-user map
        chat_logger.py        ChatLogger: reads/writes JSON log files
        chat_logs/            Auto-created directory for broadcast.json and dm-*.json
    client/
        client_main.py        Entry point - reads config and launches AppGui
        app_gui.py            AppGui: main window, orchestrates all components
        control_bar.py        ControlBar: top connect/disconnect bar
        sidebar_panel.py      SidebarPanel: broadcast button + online user list
        chat_view.py          ChatView: header, scrollable history, input bar
        chat_client.py        ChatClient: TCP socket management and sends
        network_receiver.py   NetworkReceiver: background socket-reading thread
        emoji_processor.py    EmojiProcessor: shortcode-to-emoji replacement
    docs/
        README.md             This file
        architecture.drawio   Draw.io architecture diagram
```

---

## Requirements

- Python 3.10+ (uses `tuple[bool, str]` PEP 585 type hints)
- Standard library only: `tkinter`, `socket`, `threading`, `json`, `glob`, `re`, `datetime`, `os`, `sys`

No third-party packages needed.

---

## Quick Start

### 1. Start the server

Open a terminal in the `chat_application/` directory:

```bash
python server/server_main.py
```

The server binds to `localhost:5555` by default (configurable in `config.json`).

### 2. Launch one or more clients

Open a separate terminal (or multiple terminals) in the same directory:

```bash
python client/client_main.py
```

Click **Connect 🟢**, enter a username, and start chatting.

---

## Configuration

Edit `config.json` to change the server address:

```json
{
  "host": "localhost",
  "port": 5555
}
```

Both the server and client read the same file.

---

## Username Rules

| Rule | Detail |
|------|--------|
| Allowed characters | Letters (`A-Z`, `a-z`), digits (`0-9`), underscore (`_`) |
| Length | 1 to 20 characters |
| Reserved handles | `BROADCAST`, `SYSTEM` |
| Uniqueness | Must not match any currently connected username |

---

## Chat Protocol

All messages are newline-terminated JSON objects sent over a plain TCP socket.

| Direction | Type | Key fields |
|-----------|------|------------|
| Client → Server | `LOGIN` | `username` |
| Server → Client | `LOGIN_OK` | `users`, `history` |
| Server → Client | `LOGIN_ERR` | `reason` |
| Client → Server | `MSG` | `target`, `text` |
| Server → Client | `MSG` | `target`, `sender`, `text`, `timestamp` |
| Server → Client | `USERS` | `users` |
| Server → Client | `SYS` | `text`, `timestamp` |
| Client → Server | `LOGOUT` | _(none)_ |

---

## Persistence

Chat logs are written to `server/chat_logs/`:

| File | Contents |
|------|----------|
| `broadcast.json` | All public broadcast messages |
| `dm-<a>-<b>.json` | DM thread between users `a` and `b` (names sorted alphabetically) |

Only `MSG`-type messages are persisted; system notifications are ephemeral.

---

## Emoji Shortcodes

| Shortcode | Emoji |
|-----------|-------|
| `:birthday:` | 🎂 |
| `:haha:` | 🤣 |
| `:lol:` | 😂 |
| `:fire:` | 🔥 |
| `:like:` | 👍 |
| `:check:` | ✅ |
| `:)` | 😊 |
| `:(` | 😢 |
| `<3` | ❤️ |

---

## Design Notes

- **One class per file** throughout the project.
- **Thread safety**: `UserRegistry` and `ChatLogger` use `threading.Lock`. All GUI updates from the background `NetworkReceiver` thread are dispatched to the main thread via `root.after(0, ...)`.
- **Separation of concerns**: the server has no GUI dependency; the client has no persistence dependency.
- **DM log filenames** use `-` as the pair separator (not `_`) because `-` is not an allowed username character, making the filename unambiguous even for usernames that contain underscores.
