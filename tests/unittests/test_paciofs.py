import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "paciofs"))
sys.path.append(os.path.join(os.path.dirname(__file__)))


import unittest.mock
import threading
import unittest
import logging
import random
import queue
import time
import os
import paciofs
import module

logging.disable(logging.CRITICAL)


class MockBlockchain(module.Module):
    def __init__(self):
        self.log = []
        self.lock = threading.Lock()

    def append(self, message):
        with self.lock:
            self.log.append(message)

    def getledger(self, txid):
        with self.lock:
            if txid >= len(self.log):
                return None
            return self.log[txid]


class MockBroadcast(module.Module):
    def __init__(self):
        self.head = 0
        self.stop_event = threading.Event()
        self.pubkeyhash = random.randint(0, 2 ** 30)
        self.queue = queue.Queue()

    def broadcast(self, message):
        self.southbound.append(message=(self.pubkeyhash, "txid", message))

    def _timeout_deliver(self):
        while not self.stop_event.is_set():
            self.southbound.getledger(self.head)
            message = self.southbound.getledger(self.head)
            if message is not None:
                self.head = self.head + 1
                try:
                    self.queue.put((message[0], message[1], message[2]))
                except Exception as e:
                    # print(e)
                    pass

    def deliver(self, blocking=False):
        if blocking == False:
            try:
                return self.queue.get_nowait()
            except:
                raise Exception({"error": "nothing to deliver"})
        else:
            return self.queue.get()

    def _start(self):
        threading.Thread(target=self._timeout_deliver, daemon=True).start()

    def _stop(self):
        self.stop_event.set()


class TestPacioFS(unittest.TestCase):
    def test_permissioned(self):
        for fs in self.filesystems:
            fs._accept = lambda x: False

        b = MockBlockchain()
        b._start()
        bc = MockBroadcast()
        filesystem = paciofs.PacioFS()
        bc._register_southbound(b)
        bc._register_northbound(filesystem)
        bc._start()
        filesystem._register_southbound(bc)
        filesystem._start()

        time.sleep(1)

        filename = "vol2.txt"
        payload = "vol2".encode()
        filesystem.create(filename, 0o777)
        fh = filesystem.open(filename, os.O_WRONLY)
        filesystem.write(filename, payload, 0, fh)
        filesystem.release(filename, fh)

        # wait for changes to propagate
        time.sleep(5)

        # assert file writte to this volume
        self.assertTrue(filename in list(filesystem.readdir("/", None)))
        fh = filesystem.open(filename, os.O_RDONLY)
        self.assertEqual(payload, filesystem.read(filename, 1024, 0, fh))
        filesystem.release(filename, fh)

        # assert file not writte to other volumes
        for i, fs in enumerate(self.filesystems):
            self.assertFalse(filename in list(fs.readdir("/", None)))

        filesystem._stop()
        bc._stop()
        b._stop()

    def test_verify(self):
        for i, fs in enumerate(self.filesystems):
            dirname = str(i) + str(i)
            filename = str(i)
            payload = str(i).encode()
            fs.create(filename, 0o777)
            fh = fs.open(filename, os.O_WRONLY)
            fs.write(filename, payload, 0, fh)
            fs.release(filename, fh)
            fs.mkdir(dirname, 755)

        # wait for changes to propagate
        time.sleep(5)

        # assert that FS is verified
        for i, fs in enumerate(self.filesystems):
            self.assertTrue(fs._verify())

        # unauthorized change of file system
        for i, fs in enumerate(self.filesystems):
            dirname = str(i) + str(i)
            filename = str(i)
            payload = "unauthorizedchange".encode()
            fh = fs.filesystem.open(filename, os.O_WRONLY)
            fs.filesystem.write(filename, payload, 0, fh)
            fs.filesystem.release(filename, fh)

        # assert that FS not verified
        for i, fs in enumerate(self.filesystems):
            self.assertFalse(fs._verify())

    def test_paciofs(self):
        for i, fs in enumerate(self.filesystems):
            dirname = str(i) + str(i)
            filename = str(i)
            payload = str(i).encode()
            fs.create(filename, 0o777)
            fh = fs.open(filename, os.O_WRONLY)
            fs.write(filename, payload, 0, fh)
            fs.release(filename, fh)
            fs.mkdir(dirname, 755)

        # wait for changes to propagate
        time.sleep(5)

        for i, fs in enumerate(self.filesystems):
            for j, _ in enumerate(self.filesystems):
                dirname = str(j) + str(j)
                filename = str(j)
                payload = str(j).encode()
                self.assertTrue(filename in list(fs.readdir("/", None)))
                fh = fs.open(filename, os.O_RDONLY)
                self.assertEqual(payload, fs.read(filename, 1024, 0, fh))
                fs.release(filename, fh)
                self.assertTrue(dirname in list(fs.readdir("/", None)))

    def test_multi_volume(self):
        b = MockBlockchain()
        b._start()
        bc = MockBroadcast()
        filesystem = paciofs.PacioFS("volume2")
        bc._register_southbound(b)
        bc._register_northbound(filesystem)
        bc._start()
        filesystem._register_southbound(bc)
        filesystem._start()

        time.sleep(1)

        filename = "vol2.txt"
        payload = "vol2".encode()
        filesystem.create(filename, 0o777)
        fh = filesystem.open(filename, os.O_WRONLY)
        filesystem.write(filename, payload, 0, fh)
        filesystem.release(filename, fh)

        # wait for changes to propagate
        time.sleep(5)

        # assert file writte to this volume "volume2"
        self.assertTrue(filename in list(filesystem.readdir("/", None)))
        fh = filesystem.open(filename, os.O_RDONLY)
        self.assertEqual(payload, filesystem.read(filename, 1024, 0, fh))
        filesystem.release(filename, fh)

        # assert file not writte to other volumes
        for i, fs in enumerate(self.filesystems):
            self.assertFalse(filename in list(fs.readdir("/", None)))

        filesystem._stop()
        bc._stop()
        b._stop()

    def setUp(self):
        n_filesystems = 5
        self.filesystems = []
        self.broadcasts = []

        self.b = MockBlockchain()
        self.b._start()

        for _ in range(n_filesystems):
            bc = MockBroadcast()
            bc._register_southbound(self.b)
            filesystem = paciofs.PacioFS()
            bc._register_northbound(filesystem)
            filesystem._register_southbound(bc)
            bc._start()
            filesystem._start()
            self.broadcasts.append(bc)
            self.filesystems.append(filesystem)

        time.sleep(1)

    def tearDown(self):
        for fs in self.filesystems:
            fs._stop()
        for bc in self.broadcasts:
            bc._stop()
        self.b._stop()
