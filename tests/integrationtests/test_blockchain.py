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
        n_blockchains = 10
        self.blockchains = []

        b = blockchain.Blockchain()
        b._create()
        b._start()
        self.blockchains.append(b)

        for i in range(n_blockchains - 1):
            b2 = blockchain.Blockchain(chainname=b.getinfo()["nodeaddress"])
            b2._start()
            self.blockchains.append(b2)

    def tearDown(self):
        for b in self.blockchains:
            b._stop()

    def test_more_than_one_miner(self):
        time.sleep(120)
        for b in self.blockchains:
            bbh = b.getbestblockhash()
            ledger = []
            miners = []
            while bbh is not None:
                ledger.append(bbh)
                miner = b.getblock(bbh, 1)["miner"]
                miners.append(miner)
                bbh = b.getblock(bbh, 1).get("previousblockhash", None)
            ledger.reverse()
            miners.reverse()
            self.assertTrue(
                len(set(miners)) > (float(len(self.blockchains)) / 2.0)
                and len(set(miners)) > 1
            )
