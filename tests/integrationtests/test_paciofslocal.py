import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "paciofs"))
sys.path.append(os.path.join(os.path.dirname(__file__)))


import unittest.mock
import unittest
import argparse
import logging
import filecmp
import time
import os
import tpb.tamperproofbroadcast as tamperproofbroadcast
import paciofs
import paciofslocal
import tpb.multichain as multichain

logging.disable(logging.CRITICAL)


class TestPacioFS(unittest.TestCase):
    def setUp(self):
        n_processes = 2
        self.broadcasts = []
        self.filesystems = []
        self.paciofslocals = []
        self.mountpoints = []

        self.b = multichain.MultiChain(create=True)
        self.b._create()
        self.b._start()
        time.sleep(10)  # wait for boot up
        keypairs = [self.b._create_funded_keypair() for _ in range(n_processes)]

        for keypair, i in zip(keypairs, range(n_processes)):
            args = argparse.Namespace(
                protocol="fotb",
                fotb_privkey=keypair[0],
                fotb_pubkeyhash=keypair[1],
                fotb_prevtxhash=keypair[2],
                multichain_chainname=self.b.getinfo()["nodeaddress"],
                multichain_create=True,
            )
            tpb = tamperproofbroadcast.TamperProofBroadcast._Init(args)
            tpb._create()
            tpb._start()
            self.broadcasts.append(tpb)
        time.sleep(10)  # wait for boot up

        for i in range(n_processes):
            filesystem = paciofs.PacioFS()
            self.broadcasts[i]._register_northbound(filesystem)
            filesystem._register_southbound(self.broadcasts[i])
            filesystem._create()
            filesystem._start()
            self.filesystems.append(filesystem)

        time.sleep(20)

        for pfs in self.filesystems:
            pfsl = paciofslocal.PacioFSLocal()
            pfsl._register_southbound(pfs)
            mountpoint = pfsl.mountpoint
            pfsl._start(daemon=True)
            self.mountpoints.append(mountpoint)
            self.paciofslocals.append(pfsl)

        time.sleep(10)

    def tearDown(self):
        for pfsl in self.paciofslocals:
            pfsl._stop()
            pfsl._uncreate()
        for fs in self.filesystems:
            fs._stop()
            fs._uncreate()
        for bc in self.broadcasts:
            bc._stop()
            fs._uncreate()
        self.b._stop()
        self.b._uncreate()

    def test_paciofs_large_write(self):
        with open(os.path.join(self.mountpoints[0], "large_write"), "wb") as f:
            for _ in range(10):  # 10 kB
                random_word = os.urandom(2 ** 10)
                f.write(random_word)

        time.sleep(60)

        for mountpoint in self.mountpoints:
            self.assertTrue(
                filecmp.cmp(
                    os.path.join(self.mountpoints[0], "large_write"),
                    os.path.join(mountpoint, "large_write"),
                )
            )
