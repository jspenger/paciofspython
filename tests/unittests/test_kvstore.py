import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "paciofs"))
sys.path.append(os.path.join(os.path.dirname(__file__)))


import unittest
import logging
import kvstore

logging.disable(logging.CRITICAL)


class TestKVStore(unittest.TestCase):
    def test_kvstore(self):
        kvs = kvstore.KVStore()
        for i in range(10):
            for j in range(10):
                kvs[j] = i
        for i in range(10):
            self.assertEqual(kvs[i], list(range(10)))
