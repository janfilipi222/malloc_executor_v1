import socket
import json
import threading
import selectors
import time
from domain.model.actions import TCPMsg, SendToTCP
from application.event_bus import EventBus

class TCPServer(threading.Thread):

    _running = False

    def __init__(self, event_bus: EventBus, host: str, port: int):
        super().__init__(target=self._run, daemon=True)
        self._bus = event_bus
        self._host = host
        self._port = port

        self._bus.subscribe(SendToTCP, self._handle_send_to_tcp)

        self._selector = selectors.DefaultSelector()
        
        self._server_socket: socket.socket | None = None

    def _handle_send_to_tcp(self, action: SendToTCP):
        print("from server sending: ", action.msg)

    def fire(self):

        self._running = True

        self._server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        self._server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )
        self._server_socket.setblocking(True)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen()

        self._selector.register(
            self._server_socket,
            selectors.EVENT_READ
        )

        self.start()


    def _run(self) -> None:
        while self._running:

            events = self._selector.select()

            for key, mask in events:
                if key.fileobj is self._server_socket:
                    client, address = self._server_socket.accept()
                    client.setblocking(False)

                    self._selector.register(
                        client,
                        selectors.EVENT_READ,
                        data={
                            "state": "handshake",
                            "id": "unknown"
                        }
                    )


                    print("\nnew client: ", address)
                    self.broadcast(f"you as the new client has this address: {address}")

                else:
                    client: socket.socket = key.fileobj

                    try:
                        buf = client.recv(1024)
                    except (ConnectionResetError, ConnectionAbortedError):                        
                        print("\033[90mClient connection closed unexpectedly\033[0m")
                        self._close_client(client)
                        continue
                    try:

                        if not buf:
                            self._close_client(client)
                            continue

                        data = buf.decode("utf-8")
                        messages = data.split("\n")
                        print("big msg: ", messages)
                        for message in messages[:-1]:
                            print("msg: ", message)
                            dict_msg = json.loads(message)
                            addr, port = client.getpeername()
                            # print(f"\nfrom {port} received: {message}")

                            if key.data["state"] == "handshake":
                                # print("first msg")
                                if "id" in dict_msg:
                                    key.data["state"] = "connected"
                                    key.data["id"] = dict_msg["id"]
                                else:
                                    self._bus.emit(TCPMsg(
                                        "unknown",
                                        dict_msg
                                    ))
                            else:
                                self._bus.emit(TCPMsg(
                                    key.data["id"],
                                    dict_msg
                                ))

                            # print("key.data", key.data)
                            
                            client.sendall(json.dumps(
                                {"status": "OK"}
                                ).encode("utf-8")
                            )


                    except ConnectionResetError:
                        self._close_client(client)

                    except OSError as error:
                        print(f"Socket error: {error}")
                        self._close_client(client)


    def broadcast(self, msg: dict):
        data = json.dumps(msg).encode("utf-8")
        for key in self._selector.get_map().values():
            soc: socket.socket = key.fileobj
            if soc is self._server_socket:
                continue
            soc.sendall(data)


    def _close_client(self, client: socket.socket):
        addr, port = client.getpeername()
        try:
            self._selector.unregister(client)
        except KeyError:
            pass

        print(f"\033[90mClient unregistered {(addr, port)}\033[0m")

        client.close()

    def stop(self):
        self._running = False
        if self._server_socket is not None:
            self._selector.unregister(self._server_socket)
            self._server_socket.close()
            self._server_socket = None
