import sys

sys.path.append("paciofs")

import unittest.mock
import unittest
import logging
import filecmp
import time
import os
import tamperproofbroadcast
import paciofs
import paciofslocal
import blockchain

logging.disable(logging.CRITICAL)


class TestPacioFS(unittest.TestCase):
    def setUp(self):
        n_blockchains = 3
        self.blockchains = []
        self.broadcasts = []
        self.filesystems = []
        self.paciofslocals = []
        self.mountpoints = []

        b = blockchain.Blockchain()
        b._create()
        b._start()
        self.blockchains.append(b)

        keypairs = [b._create_funded_keypair() for _ in range(n_blockchains)]

        for i in range(n_blockchains - 1):
            b2 = blockchain.Blockchain(chainname=b.getinfo()["nodeaddress"])
            b2._start()
            self.blockchains.append(b2)

        for keypair, b in zip(keypairs, self.blockchains):
            bc = tamperproofbroadcast.TamperProofBroadcast(
                keypair[0], keypair[1], keypair[2]
            )
            pfs = paciofs.PacioFS()
            bc._register_southbound(b)
            bc._register_northbound(pfs)
            bc._start()
            self.broadcasts.append(bc)
            pfs._register_southbound(bc)
            pfs._start()
            self.filesystems.append(pfs)

        for pfs in self.filesystems:
            pfsl = paciofslocal.PacioFSLocal()
            pfsl._register_southbound(pfs)
            mountpoint = pfsl.mountpoint
            pfsl._start(daemon=True)
            self.mountpoints.append(mountpoint)
            self.paciofslocals.append(pfsl)

    def tearDown(self):
        for pfs in self.filesystems:
            pfs._stop()
        for bc in self.broadcasts:
            bc._stop()
        for b in self.blockchains:
            b._stop()

    def test_paciofs_large_write(self):
        with open(os.path.join(self.mountpoints[0], "large_write"), "wb") as f:
            for _ in range(100):  # 100 MB
                random_word = os.urandom(2 ** 20)
                f.write(random_word)

        time.sleep(300)

        for mountpoint in self.mountpoints:
            self.assertTrue(
                filecmp.cmp(
                    os.path.join(self.mountpoints[0], "large_write"),
                    os.path.join(mountpoint, "large_write"),
                )
            )
