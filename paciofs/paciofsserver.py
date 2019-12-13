import logging.config
import port_for
import logging
import rpyc
import sys
import os
import blockchainbroadcast
import blockchainfs
import blockchain
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("paciofsserver")


class PacioFSServer(module.Module):
    def __init__(self, host="localhost", port=None):
        self.host = host
        self.port = port
        if self.port == None:
            self.port = port_for.select_random()

    def _start(self):
        self._handle_exit(sys.exit)
        logger.info("starting PacioFSServer at %s:%s" % (self.host, self.port))
        server = rpyc.utils.server.ThreadedServer(
            self.southbound,
            hostname=self.host,
            port=self.port,
            protocol_config={"allow_all_attrs": True},
        )
        server.start()
        self._handle_exit(server.close)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        parents=[
            PacioFSServer._Parser(),
            blockchainfs.BlockchainFS._Parser(),
            blockchainbroadcast.BlockchainBroadcast._Parser(),
            blockchain.Blockchain._Parser(),
        ]
    )
    parser.add_argument("--logginglevel", default="INFO")
    args = parser.parse_args()
    logging.getLogger().setLevel(args.logginglevel)

    b = blockchain.Blockchain._Init(args)
    bb = blockchainbroadcast.BlockchainBroadcast._Init(args)
    bfs = blockchainfs.BlockchainFS._Init(args)
    pfss = PacioFSServer._Init(args)

    bb._register_southbound(b)
    bb._register_northbound(bfs)
    bfs._register_southbound(bb)
    pfss._register_southbound(bfs)

    b._create()
    b._start()
    bb._create()
    bb._start()
    bfs._create()
    bfs._start()
    pfss._create()
    pfss._start()
