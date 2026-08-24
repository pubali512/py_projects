"""Entry point for the chat server.

Usage (run from the chat_application/ directory):
    python server/server_main.py

Reads host and port from config.json located one level above this file.
"""

import json
import os
import sys

# Allow imports from the project root (for the common package).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.chat_server import ChatServer


def load_config() -> dict:
    """
    Read config.json from the project root.

    :return: Dict with host and port keys.
    :rtype: dict
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


if __name__ == "__main__":
    config = load_config()
    server = ChatServer(host=config.get("host", "localhost"), port=config.get("port", 5555))
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()
