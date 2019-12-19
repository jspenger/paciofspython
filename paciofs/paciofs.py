import logging.config
import threading
import tempfile
import logging
import inspect
import hashlib
import shutil
import time
import fuse
import rpyc
import sys
import os
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
    def register_broadcast(self, broadcast):
        self.southbound = broadcast

    def _decorator(self, f):
        def _upon_fsapi(*args, **kwargs):
            logger.debug("upon FSAPI: %s", (f.__name__, *args))
            if f.__name__ in statechangingfunctions:
                logger.debug("trigger Broadcast: %s", (f.__name__, *args))
                try:
                    if f.__name__ == "write":
                        self.southbound.broadcast(
                            message=(
                                f.__name__,
                                args[0],
                                (hashlib.sha256(args[1]).digest(), len(args[1])),
                                args[2],
                                args[3],
                            )
                        )
                    else:
                        self.southbound.broadcast(message=(f.__name__, *args))
                except Exception as e:
                    logger.error("error: %s" % e)
                return f(*args, **kwargs)
            else:
                return f(*args, **kwargs)

        return _upon_fsapi

    def _upon_deliver(self, pid, txid, msg):
        try:
            if pid == self.southbound.pubkeyhash:
                return
            logger.debug("upon deliver: pid=%s; txid=%s; msg=%s" % (pid, txid, msg))
            if msg[0] == "join":
                server = rpyc.connect(msg[1][0], msg[1][1])
                self.servers[pid] = server.root
                return
            elif msg[0] == "leave":
                del self.servers[pid]
                return
            self.metadata[msg[1]] = txid
            if msg[0] == "write":
                # read file from remote
                fh = self.servers[pid].open(msg[1], os.O_RDONLY)
                read = self.servers[pid].read(msg[1], msg[2][1], msg[3], fh)
                read = read[0 : msg[2][1]]
                self.servers[pid].release(msg[1], fh)
                # write file local
                if hashlib.sha256(read).digest() != msg[2][0]:
                    logger.error(
                        "error: read data does not match verified data %s %s"
                        % (hashlib.sha256(read).digest(), msg[2][0])
                    )
                fh = self.filesystem.open(msg[1], os.O_WRONLY)
                self.filesystem.write(msg[1], read, msg[3], fh)
                self.filesystem.release(msg[1], fh)
            else:
                getattr(self.filesystem, msg[0])(*msg[1:])
        except Exception as e:
            logger.error("error: %s" % e)
            raise

    def _start(self):
        time.sleep(3)
        server = rpyc.utils.server.ThreadedServer(
            self, protocol_config={"safe_attrs": set(["read", "open", "release"]),}
        )
        threading.Thread(target=server.start, daemon=True).start()
        self._handle_exit(server.close)
        logger.debug("joining")
        message = ("join", (server.host, server.port))
        self.southbound.broadcast(message)

    def _stop(self):
        logger.debug("leaving")
        message = ("leave",)
        self.southbound.broadcast(message)

    def __init__(self, volume=None):
        self.volume = volume
        if self.volume == None:
            self.volume = tempfile.mkdtemp()
            self._handle_exit(lambda: shutil.rmtree(self.volume, ignore_errors=True))
        if not os.path.isdir(self.volume) and not os.path.isfile(self.volume):
            os.mkdir(self.volume)
        elif os.path.isfile(self.volume):
            raise Exception("%s is not a valid path" % self.volume)

        logger.info("creating blockchainfilesystem at volume=%s" % (self.volume))
        self.metadata = kvstore.KVStore()
        self.filesystem = passthrough.Passthrough(self.volume)
        for name, method in inspect.getmembers(self.filesystem):
            if name[0] != "_" and method is not None:
                setattr(self, name, self._decorator(method))
        self.servers = {}
