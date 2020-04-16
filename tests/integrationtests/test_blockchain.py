import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "paciofs"))
sys.path.append(os.path.join(os.path.dirname(__file__)))


import unittest.mock
import unittest
import logging
import time
import tpb.multichain as multichain

logging.disable(logging.CRITICAL)


class TestBlockchain(unittest.TestCase):
    def setUp(self):
        n_blockchains = 3
        self.blockchains = []

        b = multichain.MultiChain(create=True)
        b._create()
        b._start()
        self.blockchains.append(b)

        for i in range(n_blockchains - 1):
            b2 = multichain.MultiChain(chainname=b.getinfo()["nodeaddress"], create=True)
            b2._create()
            b2._start()
            self.blockchains.append(b2)

    def tearDown(self):
        for b in self.blockchains:
            b._stop()
            b._uncreate()

    def test_more_than_one_miner(self):
        time.sleep(60)
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
