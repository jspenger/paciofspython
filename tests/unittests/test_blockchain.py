import sys

sys.path.append("paciofs")

import unittest
import logging
import blockchain

logging.disable(logging.CRITICAL)


class TestBlockchain(unittest.TestCase):
    def test_blockchain(self):
        b1 = blockchain.Blockchain()
        b1._create()
        b1._start()
        b2 = blockchain.Blockchain(chainname=b1.getinfo()["nodeaddress"])
        b2._start()
        b3 = blockchain.Blockchain(
            rpcuser=b1.rpcuser,
            rpcpasswd=b1.rpcpasswd,
            chainname=b1.chainname,
            rpchost=b1.rpchost,
            rpcport=b1.rpcport,
        )
        self.assertEqual(b1.getinfo()["description"], b2.getinfo()["description"])
        self.assertEqual(b1.getinfo()["description"], b3.getinfo()["description"])
        b1._stop()
        b2._stop()
