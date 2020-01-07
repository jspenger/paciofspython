import logging.config
import threading
import tempfile
import logging
import inspect
import hashlib
import filecmp
import shutil
import socket
import pickle
import queue
import time
import fuse
import rpyc
import sys
import os
import dictserver
import passthrough
import kvstore
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
            returnvalue = f(*args, **kwargs)
            if f.__name__ in statechangingfunctions:
                logger.debug("trigger Broadcast: %s", (f.__name__, *args))
                try:
                    msg = (f.__name__, *args)
                    obfuscatedmsg = hashlib.sha256(pickle.dumps(msg)).digest()
                    self.dict.put(obfuscatedmsg, msg)
                    self.southbound.broadcast(message=obfuscatedmsg)
                except Exception as e:
                    logger.error("error: %s" % e)
            return returnvalue

        return _upon_fsapi

    def _upon_deliver(self, pid, txid, obfuscated_msg):
        if obfuscated_msg[0] == "join":
            logger.debug(
                "upon deliver: pid=%s; txid=%s; msg=%s" % (pid, txid, obfuscated_msg)
            )
            self.dict.join(pid, obfuscated_msg[1])
        elif pid == self.southbound.pubkeyhash:
            logger.debug(
                "upon deliver: pid=%s; txid=%s; obfuscated_msg=%s"
                % (pid, txid, obfuscated_msg)
            )
            msg = self.dict.get(obfuscated_msg)
            self.log.append((pid, txid, obfuscated_msg, msg))
            if msg[0] == "write":
                fh = self.filesystem.open(msg[1], os.O_WRONLY)
                self.filesystem.write(msg[1], msg[2], msg[3], fh)
                self.filesystem.release(msg[1], fh)
            else:
                getattr(self.filesystem, msg[0])(*msg[1:])
        elif pid in self.dict.servers:
            logger.debug(
                "upon deliver: pid=%s; txid=%s; obfuscated_msg=%s"
                % (pid, txid, obfuscated_msg)
            )
            msg = self.dict.get_remote(obfuscated_msg)
            self.dict.put(obfuscated_msg, msg)
            self.log.append((pid, txid, obfuscated_msg, msg))
            if msg[0] == "write":
                fh = self.filesystem.open(msg[1], os.O_WRONLY)
                self.filesystem.write(msg[1], msg[2], msg[3], fh)
                self.filesystem.release(msg[1], fh)
            else:
                getattr(self.filesystem, msg[0])(*msg[1:])

    def _verify(self):
        volume = tempfile.mkdtemp()
        self._handle_exit(lambda: shutil.rmtree(volume, ignore_errors=True))
        fs = passthrough.Passthrough(volume)
        for _, _, obfuscated_msg, msg in self.log:
            if obfuscated_msg != hashlib.sha256(pickle.dumps(msg)).digest():
                return False
            if msg[0] == "write":
                fh = fs.open(msg[1], os.O_WRONLY)
                fs.write(msg[1], msg[2], msg[3], fh)
                fs.release(msg[1], fh)
            else:
                getattr(fs, msg[0])(*msg[1:])
        cmp = filecmp.dircmp(volume, self.volume)
        if len(cmp.left_only) > 0 or len(cmp.right_only) > 0 or len(cmp.diff_files) > 0:
            shutil.rmtree(volume, ignore_errors=True)
            return False
        else:
            shutil.rmtree(volume, ignore_errors=True)
            return True

    def _start(self):
        self.dict._start()
        message = ("join", self.dict.get_address())
        self.southbound.broadcast(message)

    def _stop(self):
        self.dict._stop()
        self.stop_event.set()

    def __init__(self, volume=None):
        self.stop_event = threading.Event()
        self.dict = dictserver.DictServer()
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
