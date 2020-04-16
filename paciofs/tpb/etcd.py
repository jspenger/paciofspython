import multiprocessing
import logging.config
import threading
import tempfile
import binascii
import retrying
import port_for
import logging
import pickle
import shutil
import queue
import etcd3
import time
import os
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("etcd")


class _ETCDBroadcast(module.Module):
    def __init__(self, host="localhost", port="2379", queuesize=128):
        self.host = host
        self.port = port
        self.queuesize = queuesize
        self.queue = queue.Queue(maxsize=queuesize)
        self.cancel = None

    def broadcast(self, message):
        try:
            self.etcdclient.put("broadcast", self._pack(message))
        except Exception as e:
            time.sleep(0.1)
            raise Exception({"error": "failed to broadcast message"})

    def deliver(self):
        try:
            return self.queue.get_nowait()
        except:
            raise Exception("nothing to deliver")

    def _deliver(self, start_revision=1):
        try:
            try:
                iter, self.cancel = self.etcdclient.watch(
                    "broadcast", start_revision=start_revision
                )
                for i, message in enumerate(iter):
                    self.queue.put(self._unpack(message._event.kv.value))
                    start_revision = message._event.kv.mod_revision + 1
                self.cancel()
            except etcd3.exceptions.RevisionCompactedError as e:
                iter, self.cancel = self.etcdclient.watch(
                    "broadcast", start_revision=e.compacted_revision
                )
                for i, message in enumerate(iter):
                    self.queue.put(self._unpack(message._event.kv.value))
                self.cancel()
        except etcd3.exceptions.ConnectionFailedError as e:
            time.sleep(1)
            self._deliver(start_revision=start_revision)

    def _start(self):
        self.etcdclient = etcd3.client(
            host=self.host,
            port=self.port,
            grpc_options={
                "grpc.max_send_message_length": -1,
                "grpc.max_receive_message_length": -1,
            }.items(),
        )
        self.etcdclient.status()
        threading.Thread(target=self._deliver, daemon=True).start()

    def _stop(self):
        del self.etcdclient

    def _create(self):
        datadir = tempfile.mkdtemp()
        self._handle_exit(lambda: shutil.rmtree(datadir, ignore_errors=True))
        self._execute_command(
            "etcd --listen-client-urls=http://%s:%s --advertise-client-urls=http://%s:%s --data-dir=%s --listen-peer-urls=http://localhost:%s"
            % (
                self.host,
                self.port,
                self.host,
                self.port,
                datadir,
                port_for.select_random(),
            ),
            daemon=True,
        )
        self._execute_command(
            "etcdctl --endpoints=http://%s:%s endpoint status" % (self.host, self.port),
        )


class _BatchingBroadcast(module.Module):
    def __init__(self, batchsize=128):
        self.batch = [None] * batchsize
        self.nextpos = 0
        self.batchsize = batchsize
        self.deliverbatch = [None] * batchsize
        self.delivernextpos = batchsize
        self.queue = queue.Queue(maxsize=batchsize)
        self.stop_event = threading.Event()

    def broadcast(self, message):
        self.batch[self.nextpos] = message
        if self.nextpos == self.batchsize - 1:
            self.southbound.broadcast(self.batch)
            self.nextpos = 0
        else:
            self.nextpos = self.nextpos + 1

    def deliver(self, blocking=False):
        if blocking == False:
            try:
                return self.queue.get_nowait()
            except:
                raise Exception({"error": "no message to deliver"})
        else:
            return self.queue.get()

    def _deliver(self):
        while not self.stop_event.is_set():
            try:
                for message in self.southbound.deliver():
                    self.queue.put(message)
            except:
                pass

    def _start(self):
        threading.Thread(target=self._deliver, daemon=True).start()

    def _stop(self):
        self.stop_event.set()
        time.sleep(1)


class ETCD(module.Module):
    def __init__(
        self, host=None, port=None, queuesize=128, batchsize=128, create=False
    ):
        self.port = port
        self.host = host
        self.queuesize = int(queuesize)
        self.batchsize = int(batchsize)
        self.create = bool(create)
        if self.host == None:
            self.host = "localhost"
        if self.port == None:
            self.port = port_for.select_random()
        self.etcdbroadcast = _ETCDBroadcast(
            host=self.host, port=self.port, queuesize=self.queuesize
        )
        self.batchingbroadcast = _BatchingBroadcast(batchsize=self.batchsize)
        self.etcdbroadcast._register_northbound(self.batchingbroadcast)
        self.batchingbroadcast._register_southbound(self.etcdbroadcast)

    def broadcast(self, message):
        return self.batchingbroadcast.broadcast(message)

    def deliver(self, blocking=False):
        message = self.batchingbroadcast.deliver(blocking)
        return message

    def _create(self):
        if self.create:
            logger.info("creating etcd at %s:%s" % (self.host, self.port))
            self.etcdbroadcast._create()
            self.batchingbroadcast._create()
            logger.info("finished creating etcd at %s:%s" % (self.host, self.port))

    def _uncreate(self):
        if self.create:
            logger.info("uncreating etcd")
            self.batchingbroadcast._uncreate()
            self.etcdbroadcast._uncreate()

    def _start(self):
        logger.info("starting etcd at %s:%s" % (self.host, self.port))
        self.etcdbroadcast._start()
        self.batchingbroadcast._start()
        logger.info("finished starting etcd at %s:%s" % (self.host, self.port))

    def _stop(self):
        logger.info("stopping etcd")
        self.batchingbroadcast._stop()
        self.etcdbroadcast._stop()
