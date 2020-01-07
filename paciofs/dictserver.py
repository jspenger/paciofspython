import collections
import threading
import retrying
import pickle
import socket
import random
import time


class DictServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((socket.gethostname(), 0))
        self.sock.listen(128)
        self.servers = {}
        self.dict = {}
        self.stop_event = threading.Event()

    def get_address(self):
        return self.sock.getsockname()

    def join(self, pubkey, address):
        self.servers[pubkey] = address

    def get(self, key):
        return self.dict.get(key)

    def put(self, key, value):
        self.dict[key] = value

    @retrying.retry
    def get_remote(self, key):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.connect(self.servers[random.choice(list(self.servers))])
        serversocket.sendall(pickle.dumps(key))
        value = pickle.loads(serversocket.recv(4096))
        serversocket.close()
        if value == None:
            raise
        return value

    def _listen(self):
        while not self.stop_event.is_set():
            try:
                (clientsocket, address) = self.sock.accept()
                key = pickle.loads(clientsocket.recv(4096))
                value = self.dict.get(key)
                clientsocket.sendall(pickle.dumps(value))
                clientsocket.close()
            except ConnectionAbortedError as e:
                # logger.error("error: %s" % e)
                pass

    def _start(self):
        self.stop_event.clear()
        threading.Thread(target=self._listen, daemon=True).start()

    def _stop(self):
        self.stop_event.set()
        self.sock.close()

    def __iter__(self):
        return iter(self.dict)

    def items(self):
        return self.dict.items()
