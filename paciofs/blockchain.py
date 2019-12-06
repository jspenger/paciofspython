import logging.config
import multichaincli
import tempfile
import subprocess
import threading
import retrying
import port_for
import tempfile
import logging
import signal
import shutil
import psutil
import json
import time
import os
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__),'logging.conf'))
logger = logging.getLogger('blockchain')

class Blockchain(multichaincli.Multichain, module.Module):
    def __init__(self, rpcuser='user', rpcpasswd='password', rpcport=None, rpchost='localhost', chainname=None, datadir=None):
        self.rpcuser = rpcuser
        self.rpcpasswd = rpcpasswd
        self.rpcport = rpcport
        self.rpchost = rpchost
        self.chainname = chainname
        self.datadir = datadir
        if self.rpcport == None:
            self.rpcport = port_for.select_random()
        if self.chainname == None:
            import time
            self.chainname = 'chain' + str(round(time.time()))
        if self.datadir == None:
            self.datadir = tempfile.mkdtemp()
            self._handle_exit(lambda: shutil.rmtree(self.datadir, ignore_errors=True))
        super().__init__(self.rpcuser, self.rpcpasswd, self.rpchost, self.rpcport, self.chainname.split("@")[0])

    def _create(self):
        logger.info("creating blockchain: %s" % self.chainname)
        self._execute_command("multichain-util create %s -datadir=%s -anyone-can-connect=true -anyone-can-send=true -anyone-can-receive=true" % (self.chainname, self.datadir))

    def _start(self):
        logger.info("starting blockchain daemon: %s" % (self.chainname))
        self._execute_command(
            "multichaind %s -rpcuser=%s -rpcpassword=%s -rpcport=%s -rpchost=%s -datadir=%s -port=%s"
            % (self.chainname, self.rpcuser, self.rpcpasswd, self.rpcport, self.rpchost, self.datadir, port_for.select_random())
            , daemon=True)
        logger.info("waiting for blockchain daemon")
        self._execute_command(
            "multichain-cli %s -rpcuser=%s -rpcpassword=%s -rpcport=%s -rpchost=%s -datadir=%s -rpcwait getinfo"
            % (self.chainname, self.rpcuser, self.rpcpasswd, self.rpcport, self.rpchost, self.datadir))
        logger.info("blockchain daemon started")

    def _execute_command(self, command, daemon=False):
        try:
            logger.debug("executing command: %s" % command)
            if daemon == True:
                def f():
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    _, _ = process.communicate()
                    if process.returncode != 0:
                        raise
                t = threading.Thread(target=f).start()
            else:
                result = subprocess.run(command, shell=True, capture_output=True, check=True)
                return result.stdout
        except Exception as e:
            logger.error('error: %s' % e)
            raise e

    @retrying.retry(wait_random_min=1000, wait_random_max=2000, stop_max_delay=10000)
    def _create_utxo(self, pubkeyhash):
        txid = self.send(pubkeyhash, 0)
        if 'error' in txid:
            raise Exception('error: %s' % txid)
        transaction = self.getrawtransaction(txid)
        return txid, transaction

    def _create_funded_keypair(self):
        key = self.createkeypairs()
        privkey = key[0]['privkey']
        pubkeyhash = key[0]['address']
        prevtxhash, transaction = self._create_utxo(pubkeyhash)
        return privkey, pubkeyhash, prevtxhash, transaction

if __name__ == '__main__':
    b1 = Blockchain()
    b1._create()
    b1._start()
    b2 = Blockchain(chainname=b1.getinfo()['nodeaddress'])
    b2._start()
    time.sleep(15)
    print(b1.getinfo())
    print(b2.getinfo())
    print(b1.getbestblockhash())
    print(b2.getbestblockhash())
    b3 = Blockchain(rpcuser=b1.rpcuser, rpcpasswd=b1.rpcpasswd, chainname=b1.chainname, rpchost=b1.rpchost, rpcport=b1.rpcport)
    print(b3.getinfo())
    print(b3.getbestblockhash())
