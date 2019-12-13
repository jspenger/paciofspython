import sys

sys.path.append("paciofs")

import unittest.mock
import unittest
import logging
import filecmp
import time
import os
import blockchainbroadcast
import blockchainfs
import paciofslocal
import broadcast
import blockchain

# logging.disable(logging.CRITICAL)


class TestBlockchainFS(unittest.TestCase):
    def setUp(self):
        n_blockchains = 5
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
            bc = blockchainbroadcast.BlockchainBroadcast(
                keypair[0], keypair[1], keypair[2]
            )
            filesystem = blockchainfs.BlockchainFS()
            bc._register_southbound(b)
            bc._register_northbound(filesystem)
            bc._start()
            self.broadcasts.append(bc)
            filesystem._register_southbound(bc)
            filesystem._start()
            self.filesystems.append(filesystem)

        for fs in self.filesystems:
            pfsl = paciofslocal.PacioFSLocal()
            pfsl._register_southbound(fs)
            mountpoint = pfsl.mountpoint
            pfsl._start(daemon=True)
            self.mountpoints.append(mountpoint)
            self.paciofslocals.append(pfsl)
        time.sleep(10)

    def tearDown(self):
        for fs in self.filesystems:
            fs._stop()
        for bc in self.broadcasts:
            bc._stop()
        for b in self.blockchains:
            b._stop()

    def test_blockchainfs_large_write(self):
        with open(os.path.join(self.mountpoints[0], "large_write"), "wb") as f:
            for _ in range(100):
                random_word = os.urandom(100)
                f.write(random_word)

        time.sleep(60)

        for mountpoint in self.mountpoints:
            self.assertTrue(
                filecmp.cmp(
                    os.path.join(self.mountpoints[0], "large_write"),
                    os.path.join(mountpoint, "large_write"),
                )
            )
