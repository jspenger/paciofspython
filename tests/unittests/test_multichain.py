import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "paciofs"))
sys.path.append(os.path.join(os.path.dirname(__file__)))


import unittest
import logging
import tpb.multichain as multichain

logging.disable(logging.CRITICAL)


class TestMultiChain(unittest.TestCase):
    def test_multichain(self):
        b1 = multichain.MultiChain(create=True)
        b1._create()
        b1._start()
        b2 = multichain.MultiChain(chainname=b1.getinfo()["nodeaddress"], create=True)
        b2._create()
        b2._start()
        b3 = multichain.MultiChain(
            user=b1.rpcuser,
            passwd=b1.rpcpasswd,
            chainname=b1.chainname,
            host=b1.rpchost,
            port=b1.rpcport,
        )
        b3._create()
        b3._start()
        self.assertEqual(b1.getinfo()["description"], b2.getinfo()["description"])
        self.assertEqual(b1.getinfo()["description"], b3.getinfo()["description"])
        b1._stop()
        b2._stop()
        b1._uncreate()
        b2._uncreate()
