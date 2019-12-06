import logging.config
import tempfile
import logging
import shutil
import fuse
import rpyc
import os
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__),'logging.conf'))
logger = logging.getLogger('paciofsclient')

class PacioFSClient(module.Module):
    def __init__(self, host=None, port=None, mountpoint=None):
        self.host = host
        self.port = port
        self.mountpoint = mountpoint
        if self.host == None or self.port == None:
            raise Exception('error: invalid host=%s or port=%s' % (self.host, self.port))
        if self.mountpoint == None:
            self.mountpoint = tempfile.mkdtemp()
            self._handle_exit(lambda: shutil.rmtree(self.mountpoint, ignore_errors=True))

    def _start(self):
        logger.info("starting PacioFSClient, mountpont=%s, connecting to %s:%s" % (self.mountpoint, self.host, self.port))
        fuse.FUSE(
            rpyc.connect(self.host, self.port).root,
            self.mountpoint,
            nothreads=True,
            foreground=True,
            )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(parents=[PacioFSClient._Parser()])
    parser.add_argument('--logginglevel', default='INFO')
    args = parser.parse_args()
    logging.getLogger().setLevel(args.logginglevel)

    pfsc = PacioFSClient._Init(args)

    pfsc._create()
    pfsc._start()
