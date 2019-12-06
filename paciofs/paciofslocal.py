import logging.config
import tempfile
import logging
import shutil
import fuse
import os
import blockchainbroadcast
import blockchainfs
import blockchain
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__),'logging.conf'))
logger = logging.getLogger('paciofslocal')

class PacioFSLocal(module.Module):
    def __init__(self, mountpoint=None):
        self.mountpoint = mountpoint
        if self.mountpoint == None:
            self.mountpoint = tempfile.mkdtemp()
            self._handle_exit(lambda: shutil.rmtree(self.mountpoint, ignore_errors=True))

    def _start(self):
        logger.info("starting PacioFSLocal: mountpoint=%s; volume=%s" % (self.mountpoint, self.southbound.volume))
        fuse.FUSE(self.southbound, self.mountpoint, nothreads=True, foreground=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[PacioFSLocal._Parser(), blockchainfs.BlockchainFS._Parser(), blockchainbroadcast.BlockchainBroadcast._Parser(), blockchain.Blockchain._Parser()])
    parser.add_argument('--logginglevel', default='INFO')
    args = parser.parse_args()
    logging.getLogger().setLevel(args.logginglevel)

    b = blockchain.Blockchain._Init(args)
    bb = blockchainbroadcast.BlockchainBroadcast._Init(args)
    bfs = blockchainfs.BlockchainFS._Init(args)
    pfsl = PacioFSLocal._Init(args)

    bb._register_southbound(b)
    bb._register_northbound(bfs)
    bfs._register_southbound(bb)
    pfsl._register_southbound(bfs)

    b._create()
    b._start()
    bb._create()
    bb._start()
    bfs._create()
    bfs._start()
    pfsl._create()
    pfsl._start()
