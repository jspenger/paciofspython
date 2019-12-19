import logging.config
import threading
import tempfile
import logging
import inspect
import hashlib
import shutil
import pickle
import time
import fuse
import rpyc
import sys
import os
import passthrough
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("paciofs")

statechangingfunctions = [
    "chmod",
    "chown",
    "create",
    "link",
    "mkdir",
    "mknod",
    "removexattr",
    "rename",
    "rmdir",
    "setxattr",
    "symlink",
    "truncate",
    "unlink",
    "utimens",
    "write",
]


class PacioFS(rpyc.Service, fuse.Operations, module.Module):
    def _decorator(self, f):
        def _upon_fsapi(*args, **kwargs):
            logger.debug("upon FSAPI: %s", (f.__name__, *args))
            if f.__name__ in statechangingfunctions:
                logger.debug("trigger Broadcast: %s", (f.__name__, *args))
                try:
                    msg = (f.__name__, *args)
                    obfuscatedmsg = hashlib.sha256(pickle.dumps(msg)).digest()
                    self.log.append((obfuscatedmsg, msg))
                    self.southbound.broadcast(message=msg)
                except Exception as e:
                    logger.error("error: %s" % e)
            return f(*args, **kwargs)
        return _upon_fsapi

    def _upon_deliver(self, pid, txid, msg):
        if pid == self.southbound.pubkeyhash:
            logger.debug("upon deliver: pid=%s; txid=%s; msg=%s" % (pid, txid, msg))
            self.log.append(pid, txid, msg)

    def _verify(self):
        # TODO: implement
        pass

    def __init__(self, volume=None):
        self.log = []
        self.volume = volume
        if self.volume == None:
            self.volume = tempfile.mkdtemp()
            self._handle_exit(lambda: shutil.rmtree(self.volume, ignore_errors=True))
        if not os.path.isdir(self.volume) and not os.path.isfile(self.volume):
            os.mkdir(self.volume)
        elif os.path.isfile(self.volume):
            raise Exception("%s is not a valid path" % self.volume)

        logger.info("creating blockchainfilesystem at volume=%s" % (self.volume))
        self.filesystem = passthrough.Passthrough(self.volume)
        for name, method in inspect.getmembers(self.filesystem):
            if name[0] != "_" and method is not None:
                setattr(self, name, self._decorator(method))
