import collections
import threading
import retrying
import logging
import pickle
import socket
import random
import time
import os
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("helper")


class DictServer(module.Module):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((socket.gethostname(), 0))
        self.sock.listen(128)
        self.servers = {}
        self.dict = {}
        self.stop_event = threading.Event()

    def get_address(self):
        return self.sock.getsockname()

    def add_server(self, pubkey, address):
        self.servers[pubkey] = address

    def get(self, key):
        return self.dict.get(key)

    def put(self, key, value):
        self.dict[key] = value

    @retrying.retry(wait_random_min=100, wait_random_max=2000, stop_max_delay=60000)
    def get_remote(self, key):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.connect(self.servers[random.choice(list(self.servers))])
        serversocket.sendall(pickle.dumps(key))
        value = pickle.loads(serversocket.recv(4096))
        serversocket.close()
        if value == None:
            raise Exception("could not find key: %s" % (key))
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
                logger.error("error: %s" % e)

    def _start(self):
        self.stop_event.clear()
        self._handle_exit(self._stop)
        threading.Thread(target=self._listen, daemon=True).start()

    def _stop(self):
        self.stop_event.set()
        self.sock.close()
