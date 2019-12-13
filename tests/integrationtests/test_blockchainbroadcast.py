import sys

sys.path.append("paciofs")

import unittest.mock
import unittest
import logging
import time
import blockchainbroadcast
import broadcast
import blockchain

logging.disable(logging.CRITICAL)


class TestBlockchainBroadcast(unittest.TestCase):
    def setUp(self):
        n_blockchains = 5
        self.blockchains = []
        self.broadcasts = []
        self.northbounds = []

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
            northbound = unittest.mock.MagicMock()
            self.northbounds.append(northbound)
            bc._register_southbound(b)
            bc._register_northbound(northbound)
            bc._start()
            self.broadcasts.append(bc)

    def tearDown(self):
        for bc in self.broadcasts:
            bc._stop()
        for b in self.blockchains:
            b._stop()

    def test_blockchainbroadcast(self):
        for bc in self.broadcasts:
            for i in range(10):
                bc.broadcast(i)

        time.sleep(60)

        for nb in self.northbounds:
            for bc in self.broadcasts:
                pid = bc.pubkeyhash
                for i in range(10):
                    nb._upon_deliver.assert_any_call(pid, unittest.mock.ANY, i)
