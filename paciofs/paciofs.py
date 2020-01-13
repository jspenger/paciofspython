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
import passthrough
import module
import helper

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
                    self.dictserver.put(obfuscatedmsg, msg)
                    self.southbound.broadcast(message=obfuscatedmsg)
                except Exception as e:
                    logger.error("error: %s" % e)
            return returnvalue

        return _upon_fsapi

    def _upon_deliver(self, pid, txid, obfuscatedmsg):
        if obfuscatedmsg[0] == "join" and obfuscatedmsg[2] == self.volume:
            logger.debug(
                "upon deliver: pid=%s; txid=%s; msg=%s" % (pid, txid, obfuscatedmsg)
            )
            self.dictserver.add_server(pid, obfuscatedmsg[1])
        elif pid in self.dictserver.servers and pid == self.southbound.pubkeyhash:
            logger.debug(
                "upon deliver: pid=%s; txid=%s; obfuscatedmsg=%s"
                % (pid, txid, obfuscatedmsg)
            )
            msg = self.dictserver.get(obfuscatedmsg)
            self.log.append((pid, txid, obfuscatedmsg, msg))
            if msg[0] == "write":
                fh = self.filesystem.open(msg[1], os.O_WRONLY)
                self.filesystem.write(msg[1], msg[2], msg[3], fh)
                self.filesystem.release(msg[1], fh)
            else:
                getattr(self.filesystem, msg[0])(*msg[1:])
        elif pid in self.dictserver.servers:
            logger.debug(
                "upon deliver: pid=%s; txid=%s; obfuscatedmsg=%s"
                % (pid, txid, obfuscatedmsg)
            )
            msg = self.dictserver.get_remote(obfuscatedmsg)
            self.dictserver.put(obfuscatedmsg, msg)
            self.log.append((pid, txid, obfuscatedmsg, msg))
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
        for _, _, obfuscatedmsg, msg in self.log:
            if obfuscatedmsg != hashlib.sha256(pickle.dumps(msg)).digest():
                return False
            if msg[0] == "write":
                fh = fs.open(msg[1], os.O_WRONLY)
                fs.write(msg[1], msg[2], msg[3], fh)
                fs.release(msg[1], fh)
            else:
                getattr(fs, msg[0])(*msg[1:])
        cmp = filecmp.dircmp(volume, self.fileservervolume)
        if len(cmp.left_only) > 0 or len(cmp.right_only) > 0 or len(cmp.diff_files) > 0:
            shutil.rmtree(volume, ignore_errors=True)
            return False
        else:
            shutil.rmtree(volume, ignore_errors=True)
            return True

    def _start(self):
        self.dictserver._start()
        message = ("join", self.dictserver.get_address(), self.volume)
        self.southbound.broadcast(message)

    def _stop(self):
        self.dictserver._stop()
        self.stop_event.set()

    def __init__(self, volume=None, fileservervolume=None):
        self.stop_event = threading.Event()
        self.dictserver = helper.DictServer()
        self.log = []
        self.volume = volume
        if fileservervolume == None:
            self.fileservervolume = tempfile.mkdtemp()
            self._handle_exit(
                lambda: shutil.rmtree(self.fileservervolume, ignore_errors=True)
            )
        if not os.path.isdir(self.fileservervolume) and not os.path.isfile(
            self.fileservervolume
        ):
            os.mkdir(self.fileservervolume)
        elif os.path.isfile(self.fileservervolume):
            raise Exception("%s is not a valid path" % self.fileservervolume)
        logger.info(
            "creating blockchainfilesystem at volume=%s" % (self.fileservervolume)
        )
        self.filesystem = passthrough.Passthrough(self.fileservervolume)
        for name, method in inspect.getmembers(self.filesystem):
            if name[0] != "_" and method is not None:
                setattr(self, name, self._decorator(method))
