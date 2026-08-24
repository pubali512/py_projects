"""Entry point for the chat client application.

Usage (run from the chat_application/ directory):
    python client/client_main.py

Reads host and port from config.json located one level above this file.
"""

import json
import os
import sys

# Allow imports from the project root (for the common package).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.app_gui import AppGui


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
    app = AppGui(config)
    app.run()
