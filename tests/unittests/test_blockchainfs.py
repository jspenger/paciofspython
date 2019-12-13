import sys

sys.path.append("paciofs")

import unittest.mock
import unittest
import logging
import time
import os
from paciofs import blockchainfs

logging.disable(logging.CRITICAL)


class TestBlockchainFS(unittest.TestCase):
    def test_blockchainfs(self):
        mockSouthbound = unittest.mock.MagicMock()
        bfs = blockchainfs.BlockchainFS()
        bfs._register_southbound(mockSouthbound)
        bfs._start()
        payload = b"hello world"
        filename = "a"
        bfs.create(filename, 0o777)
        fh = bfs.open(filename, os.O_WRONLY)
        bfs.write(filename, payload, 0, fh)
        bfs.release(filename, fh)
        self.assertTrue("a" in list(bfs.readdir("/", None)))
        fh = bfs.open(filename, os.O_RDONLY)
        self.assertEqual(payload, bfs.read(filename, 1024, 0, fh))
        bfs.release(filename, fh)
        bfs.mkdir("testdir", 755)
        self.assertTrue("testdir" in list(bfs.readdir("/", None)))
        msg = ["create", "b", 0o777]
        bfs._upon_deliver(1, 1, msg)
        self.assertTrue("b" in list(bfs.readdir("/", None)))
        msg = ["write", "b", payload, 0, 0]
        bfs._upon_deliver(1, 1, msg)
        fh = bfs.open("b", os.O_RDONLY)
        self.assertEqual(payload, bfs.read("b", 1024, 0, fh))
        bfs.release("b", fh)
