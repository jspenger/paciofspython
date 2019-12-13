import logging.config
import multichaincli
import retrying
import port_for
import tempfile
import logging
import shutil
import time
import sys
import os
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("blockchain")


class Blockchain(multichaincli.Multichain, module.Module):
    """Create, start, and communicate (RPC) with multichain blockchain server.

    Blockchain RPC abstraction of the multichain blockchain.
    _create a new blockchain instance, _start an multichain server, _stop any
    started clients.
    If omitting any parameters, _create will create a new multichain instance,
    and _start will start a new multichain server of that instance.
    If passing chainname of the form "chainname@host:post", then _start will
    start a new multichain server, connecting to (remote) multichain blockchain
    instance with name "chainname" at "host:port".
    If passing the rpcuser, rpcpasswd, chainname, rpchost, rpcport of a running
    multichain server, then will connect to server at passed arguments.
    """

    def __init__(
        self,
        rpcuser="user",
        rpcpasswd="password",
        rpcport=None,
        rpchost="localhost",
        chainname=None,
        datadir=None,
    ):
        self.rpcuser = rpcuser
        self.rpcpasswd = rpcpasswd
        self.rpcport = rpcport
        self.rpchost = rpchost
        self.chainname = chainname
        self.datadir = datadir
        if self.rpcport is None:
            self.rpcport = port_for.select_random()
        if self.chainname is None:
            self.chainname = "chain" + str(round(time.time()))
        if self.datadir is None:
            self.datadir = tempfile.mkdtemp()
            self._handle_exit(lambda: shutil.rmtree(self.datadir, ignore_errors=True))
        super().__init__(
            self.rpcuser,
            self.rpcpasswd,
            self.rpchost,
            self.rpcport,
            self.chainname.split("@")[0],
        )
        self._handle_exit(sys.exit)

    def _create(self):
        logger.info("creating blockchain: %s" % self.chainname)
        self._execute_command(
            "multichain-util create %s -datadir=%s -anyone-can-connect=true -anyone-can-send=true -anyone-can-receive=true -anyone-can-mine=true -target-block-time=5 -mining-turnover=1.0"
            % (self.chainname, self.datadir)
        )

    def _start(self):
        logger.info(
            "starting blockchain daemon: %s at %s:%s"
            % (self.chainname, self.rpchost, self.rpcport)
        )
        self._execute_command(
            "multichaind %s -rpcuser=%s -rpcpassword=%s -rpcport=%s -rpchost=%s -datadir=%s -port=%s"
            % (
                self.chainname,
                self.rpcuser,
                self.rpcpasswd,
                self.rpcport,
                self.rpchost,
                self.datadir,
                port_for.select_random(),
            ),
            daemon=True,
        )
        logger.info("waiting for blockchain daemon")
        self._execute_command(
            "multichain-cli %s -rpcuser=%s -rpcpassword=%s -rpcport=%s -rpchost=%s -datadir=%s -rpcwait getinfo"
            % (
                self.chainname,
                self.rpcuser,
                self.rpcpasswd,
                self.rpcport,
                self.rpchost,
                self.datadir,
            )
        )
        logger.info("blockchain daemon started")

    def _stop(self):
        logger.info("stopping blockchain daemon: %s" % (self.chainname))
        self._execute_command(
            "multichain-cli %s -rpcuser=%s -rpcpassword=%s -rpcport=%s -rpchost=%s -datadir=%s stop"
            % (
                self.chainname,
                self.rpcuser,
                self.rpcpasswd,
                self.rpcport,
                self.rpchost,
                self.datadir,
            )
        )
        logger.info("blockchain daemon stopped")

    @retrying.retry(wait_random_min=100, wait_random_max=2000, stop_max_delay=60000)
    def _create_utxo(self, pubkeyhash):
        txid = self.send(pubkeyhash, 0)
        if "error" in txid:
            raise Exception("error: %s" % txid)
        while True:
            txinfo = self.getrawtransaction(txid, 1)
            if "error" in txinfo:
                raise Exception("error: %s" % txinfo)
            break
        transaction = self.getrawtransaction(txid)
        return txid, transaction

    def _create_funded_keypair(self):
        key = self.createkeypairs()
        privkey = key[0]["privkey"]
        pubkeyhash = key[0]["address"]
        prevtxhash, transaction = self._create_utxo(pubkeyhash)
        return privkey, pubkeyhash, prevtxhash, transaction
