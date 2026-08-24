import os
import socket
import threading

from common.username_validator import UsernameValidator
from server.chat_logger import ChatLogger
from server.client_handler import ClientHandler
from server.message_router import MessageRouter
from server.user_registry import UserRegistry


class ChatServer:
    """TCP chat server that accepts client connections and creates handler thread for each client.

    How it works:
        1. Start the server and bind the server socket to the configured host and port.
        2. Wait in a loop to accept incoming client connections.
        3. For each accepted connection, create a ClientHandler and run it
           in a separate thread.

    Shutdown:
        Call stop() to signal the accept loop to exit and close the server socket.
    """

    def __init__(self, host: str, port: int) -> None:
        """
        :param host: Hostname or IP address to bind to (e.g., 'localhost').
        :type host: str
        :param port: TCP port number to listen on.
        :type port: int
        :return: None
        :rtype: None
        """
        self._host = host
        self._port = port
        self._server_socket: socket.socket = None
        self._is_running = False

        server_dir = os.path.dirname(os.path.abspath(__file__))
        self._persistence = ChatLogger(server_dir)
        self._registry = UserRegistry()
        self._router = MessageRouter(self._registry, self._persistence)
        self._validator = UsernameValidator()

    def start(self) -> None:
        """
        Server starts and waits for client connections. 

        :return: None
        :rtype: None
        """
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(10)
        self._is_running = True

        print(f"Server listening on {self._host}:{self._port}")

        while self._is_running:
            try:
                client_socket, address = self._server_socket.accept()
            except OSError:
                break

            handler = ClientHandler(
                client_socket=client_socket,
                address=address,
                router=self._router,
                registry=self._registry,
                persistence=self._persistence,
                validator=self._validator,
            )
            thread = threading.Thread(target=handler.run, daemon=True)
            thread.start()
            print(f"New connection from {address}")

        print("Server stopped.")

    def stop(self) -> None:
        """
        Stops server. 

        :return: None
        :rtype: None
        """
        self._is_running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass

    @property
    def is_running(self) -> bool:
        """
        Returns True when the server is running. 
        """
        return self._is_running
