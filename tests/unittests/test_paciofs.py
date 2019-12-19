import sys

sys.path.append("paciofs")

import unittest.mock
import unittest
import logging
import time
import os
import paciofs

logging.disable(logging.CRITICAL)


class TestPacioFS(unittest.TestCase):
    def test_paciofs(self):
        mockSouthbound = unittest.mock.MagicMock()
        pfs = paciofs.PacioFS()
        pfs._register_southbound(mockSouthbound)
        pfs._start()
        payload = b"hello world"
        filename = "a"
        pfs.create(filename, 0o777)
        fh = pfs.open(filename, os.O_WRONLY)
        pfs.write(filename, payload, 0, fh)
        pfs.release(filename, fh)
        self.assertTrue("a" in list(pfs.readdir("/", None)))
        fh = pfs.open(filename, os.O_RDONLY)
        self.assertEqual(payload, pfs.read(filename, 1024, 0, fh))
        pfs.release(filename, fh)
        pfs.mkdir("testdir", 755)
        self.assertTrue("testdir" in list(pfs.readdir("/", None)))
        msg = ["create", "b", 0o777]
        pfs._upon_deliver(1, 1, msg)
        self.assertTrue("b" in list(pfs.readdir("/", None)))
        msg = ["write", "b", payload, 0, 0]
        pfs._upon_deliver(1, 1, msg)
        fh = pfs.open("b", os.O_RDONLY)
        self.assertEqual(payload, pfs.read("b", 1024, 0, fh))
        pfs.release("b", fh)
