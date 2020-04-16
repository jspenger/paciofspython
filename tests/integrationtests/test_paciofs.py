import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "paciofs"))
sys.path.append(os.path.join(os.path.dirname(__file__)))


import unittest.mock
import unittest
import argparse
import logging
import time
import os
import tpb.tamperproofbroadcast as tamperproofbroadcast
import tpb.multichain as multichain
import paciofs

logging.disable(logging.CRITICAL)


class TestPacioFS(unittest.TestCase):
    def setUp(self):
        self.n_processes = 2
        self.broadcasts = []
        self.filesystems = []

        self.b = multichain.MultiChain(create=True)
        self.b._create()
        self.b._start()
        time.sleep(10)  # wait for boot up
        self.keypairs = [self.b._create_funded_keypair() for _ in range(self.n_processes+1)]

        for keypair, i in zip(self.keypairs, range(self.n_processes)):
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

        for i in range(self.n_processes):
            filesystem = paciofs.PacioFS()
            self.broadcasts[i]._register_northbound(filesystem)
            filesystem._register_southbound(self.broadcasts[i])
            filesystem._create()
            filesystem._start()
            self.filesystems.append(filesystem)

        time.sleep(20)

    def tearDown(self):
        for fs in self.filesystems:
            fs._stop()
            fs._uncreate()
        for bc in self.broadcasts:
            bc._stop()
            fs._uncreate()
        self.b._stop()
        self.b._uncreate()

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
        time.sleep(60)

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
        time.sleep(60)

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
        keypair = self.keypairs[self.n_processes]

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

        time.sleep(10)

        filesystem = paciofs.PacioFS(volume="volume2")
        tpb._register_northbound(filesystem)
        filesystem._register_southbound(tpb)
        filesystem._create()
        filesystem._start()

        time.sleep(20)

        filename = "vol2.txt"
        payload = "vol2".encode()
        filesystem.create(filename, 0o777)
        fh = filesystem.open(filename, os.O_WRONLY)
        filesystem.write(filename, payload, 0, fh)
        filesystem.release(filename, fh)

        # wait for changes to propagate
        time.sleep(60)

        # assert file written to this volume "volume2"
        self.assertTrue(filename in list(filesystem.readdir("/", None)))
        fh = filesystem.open(filename, os.O_RDONLY)
        self.assertEqual(payload, filesystem.read(filename, 1024, 0, fh))
        filesystem.release(filename, fh)

        # assert file not writte to other volumes
        for i, fs in enumerate(self.filesystems):
            self.assertFalse(filename in list(fs.readdir("/", None)))

        filesystem._stop()
        filesystem._uncreate()
        tpb._stop()
        tpb._uncreate()
