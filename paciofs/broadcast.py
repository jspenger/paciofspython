import threading
import binascii
import pickle
import queue
import module


class Broadcast(module.Module):
    def _pack(self, message):
        return binascii.hexlify(pickle.dumps(message)).decode()

    def _unpack(self, payload):
        return pickle.loads(binascii.unhexlify(payload))

    def __init__(self):
        self.queue = queue.Queue()
        self.pid = 1
        self.txid = 1

    def _start(self):
        threading.Thread(target=self.deliver, daemon=True).start()

    def deliver(self):
        for message in iter(self.queue.get, None):
            self.northbound._upon_deliver(self.pid, self.txid, self._unpack(message))

    def broadcast(self, message):
        self.queue.put(self._pack(message))
