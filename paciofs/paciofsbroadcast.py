import logging.config
import tempfile
import logging
import shutil
import fuse
import sys
import os
import blockchainbroadcast
import blockchain
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("paciofsbroadcast")


class PacioFSBroadcast(module.Module):
    def __init__(self):
        self._handle_exit(sys.exit)

    def _upon_deliver(self, pid, txid, message):
        print("message received: pid=%s txid=%s message=%s" % (pid, txid, message))

    def _start(self):
        logger.info("starting PacioFSBroadcast")
        while True:
            for line in sys.stdin:
                self.southbound.broadcast(line)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        parents=[
            PacioFSBroadcast._Parser(),
            blockchainbroadcast.BlockchainBroadcast._Parser(),
            blockchain.Blockchain._Parser(),
        ]
    )
    parser.add_argument("--logginglevel", default="INFO")
    args = parser.parse_args()
    logging.getLogger().setLevel(args.logginglevel)

    b = blockchain.Blockchain._Init(args)
    bb = blockchainbroadcast.BlockchainBroadcast._Init(args)
    pfb = PacioFSBroadcast._Init(args)

    bb._register_southbound(b)
    bb._register_northbound(pfb)
    pfb._register_southbound(bb)

    b._create()
    b._start()
    bb._create()
    bb._start()
    pfb._create()
    pfb._start()
    pfb._stop()
    bb._stop()
    b._stop()
