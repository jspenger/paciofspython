import logging.config
import threading
import tempfile
import logging
import shutil
import fuse
import time
import sys
import os
import tpb.tamperproofbroadcast as tamperproofbroadcast
import paciofs
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("paciofslocal")


class PacioFSLocal(module.Module):
    def __init__(self, mountpoint=None):
        self.mountpoint = mountpoint
        if self.mountpoint == None:
            self.mountpoint = tempfile.mkdtemp()
            self._handle_exit(
                lambda: shutil.rmtree(self.mountpoint, ignore_errors=True)
            )

    def _start(self, daemon=False):
        logger.info(
            "starting PacioFSLocal: mountpoint=%s; volume=%s"
            % (self.mountpoint, self.southbound.volume)
        )
        if daemon == True:
            self._handle_exit(fuse.fuse_exit)
            self._handle_exit(sys.exit)
            threading.Thread(
                target=fuse.FUSE,
                args=(self.southbound, self.mountpoint),
                kwargs=dict(nothreads=True, foreground=True),
                daemon=True,
            ).start()
            time.sleep(5)
        else:
            fuse.FUSE(self.southbound, self.mountpoint, nothreads=True, foreground=True)

    def _stop(self):
        fuse.fuse_exit()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        parents=[
            PacioFSLocal._Parser(),
            paciofs.PacioFS._Parser(),
            tamperproofbroadcast.TamperProofBroadcast._Parser(),
        ]
    )
    parser.add_argument("--logginglevel", default="INFO")
    args = parser.parse_args()
    logging.getLogger().setLevel(args.logginglevel)

    bc = tamperproofbroadcast.TamperProofBroadcast._Init(args)
    pfs = paciofs.PacioFS._Init(args)
    pfsl = PacioFSLocal._Init(args)

    bc._register_northbound(pfs)
    pfs._register_southbound(bc)
    pfsl._register_southbound(pfs)

    bc._create()
    bc._start()
    pfs._create()
    pfs._start()
    pfsl._create()
    pfsl._start()
