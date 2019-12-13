import sys

sys.path.append("paciofs")

import unittest.mock
import unittest
import logging
import time
from paciofs import broadcast

logging.disable(logging.CRITICAL)


class TestBroadcast(unittest.TestCase):
    def test_broadcast(self):
        b = broadcast.Broadcast()
        mockNorthbound = unittest.mock.MagicMock()
        b._register_northbound(mockNorthbound)
        b._start()
        for i in range(10):
            b.broadcast(i)
        time.sleep(1)
        for i in range(10):
            mockNorthbound._upon_deliver.assert_any_call(
                unittest.mock.ANY, unittest.mock.ANY, i
            )
        b._stop()
