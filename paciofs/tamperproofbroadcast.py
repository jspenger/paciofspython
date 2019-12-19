import multiprocessing
import logging.config
import threading
import retrying
import binascii
import logging
import pickle
import queue
import time
import sys
import os
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("tamperproofbroadcast")


class TamperProofBroadcast(module.Module):
    def _pack(self, message):
        return binascii.hexlify(pickle.dumps(message)).decode()

    def _unpack(self, payload):
        return pickle.loads(binascii.unhexlify(payload))

    def _createTransaction(self, privkey, pubkeyhash, prevtxhash, message):
        logger.debug(
            "creating transaction: %s", (privkey, pubkeyhash, prevtxhash, message)
        )
        payload = self._pack(message)
        inputs = [{"txid": prevtxhash, "vout": 0, "sequence": 0}]
        outputs = {pubkeyhash: 0}
        data = [payload]
        transaction = self.southbound.createrawtransaction(inputs, outputs, data)
        signedtransaction = self.southbound.signrawtransaction(
            transaction, [], [privkey]
        )["hex"]
        return signedtransaction

    def _unpackTransaction(self, txhex):
        try:
            logger.debug("unpacking transaction: %s", txhex)
            transaction = self.southbound.decoderawtransaction(txhex)
            payload = transaction["vout"][1]["data"][0]
            message = self._unpack(payload)
            pubkeyhash = self.southbound.decoderawtransaction(
                self.southbound.getrawtransaction(transaction["vin"][0]["txid"])
            )["vout"][0]["scriptPubKey"]["addresses"][0]
            txhash = transaction["txid"]
            return pubkeyhash, txhash, message
        except Exception as e:
            logger.debug("error unpacking: %s", e)

    def _sendTransaction(self, signedtransaction):
        logger.debug("sending transaction: %s", signedtransaction)
        txhash = self.southbound.sendrawtransaction(signedtransaction)
        return txhash

    def _start(self):
        if self.prevtxhash is None and self.privkey is None and self.pubkeyhash is None:
            (
                self.privkey,
                self.pubkeyhash,
                self.prevtxhash,
                transaction,
            ) = self.southbound._create_funded_keypair()
            self.lock.acquire()
            self.waiting[self.prevtxhash] = transaction
            self.lock.release()
        logger.info(
            "starting blockchain broadcast: privkey=%s pubkey=%s prevtxhash=%s"
            % (self.privkey, self.pubkeyhash, self.prevtxhash)
        )
        threading.Thread(target=self._timeout_append, daemon=True).start()
        threading.Thread(target=self._timeout_deliver, daemon=True).start()
        threading.Thread(target=self._timeout_broadcast, daemon=True).start()

    def __init__(self, privkey=None, pubkeyhash=None, prevtxhash=None):
        self.southbound = None
        self.filesystem = None
        self.waiting = {}
        self.lock = threading.Lock()
        self.ledger = [None]
        self.confirmed_height = 1
        self.privkey = privkey
        self.pubkeyhash = pubkeyhash
        self.prevtxhash = prevtxhash
        self.queue = queue.Queue()

    def broadcast(self, message):
        logger.info("upon_broadcast: %s", message)
        self.queue.put(message)

    def _timeout_broadcast(self):
        while True:
            t = time.time()
            size = 0
            messages = []
            while True:
                try:
                    message = self.queue.get_nowait()
                    messages.append(message)
                    size += sys.getsizeof(message)
                except:
                    pass
                if t + 0.1 < time.time() or size > 100000:
                    break
            if messages != []:
                signedtransaction = self._createTransaction(
                    self.privkey, self.pubkeyhash, self.prevtxhash, messages
                )
                self.prevtxhash = self._sendTransaction(signedtransaction)
                self.lock.acquire()
                self.waiting[self.prevtxhash] = signedtransaction
                self.lock.release()
            time.sleep(0.1)

    def _timeout_append(self):
        while True:
            logger.debug("upon timeout (append)")
            self.lock.acquire()
            for txhash, signedtransaction in self.waiting.items():
                logger.debug("trigger append: %s", txhash)
                self._sendTransaction(signedtransaction)
            self.lock.release()
            time.sleep(600.0)

    def _timeout_deliver(self):
        try:
            while True:
                logger.debug("upon timeout (deliver)")
                logger.debug("trigger get")
                bbh = self.southbound.getbestblockhash()
                newledger = []
                while bbh not in self.ledger:
                    newledger.append(bbh)
                    bbh = self.southbound.getblock(bbh, 1).get(
                        "previousblockhash", None
                    )
                newledger.reverse()
                self.ledger = self.ledger[: self.ledger.index(bbh) + 1]
                self.ledger.extend(newledger)

                logger.debug("upon getreturn: ledger=...%s" % self.ledger[-6:])
                for block in self.ledger[self.confirmed_height : -6]:
                    self.confirmed_height += 1
                    for transaction in self.southbound.getblock(block, 2)["tx"]:
                        try:
                            utx = self._unpackTransaction(transaction["hex"])
                            if utx == None:
                                continue
                            pid, txid, messages = utx
                            for message in messages:
                                logger.info(
                                    "trigger deliver: pid=%s; txid=%s; message=%s"
                                    % (pid, txid, message)
                                )
                                self.northbound._upon_deliver(pid, txid, message)
                            self.lock.acquire()
                            if txid in self.waiting:
                                self.waiting.pop(txid)
                            self.lock.release()
                        except Exception as e:
                            logger.error("error: %s", e)
                time.sleep(5.0)
        except Exception as e:
            logger.error("error: %s", e)
            raise
