import logging.config
import port_for
import logging
import rpyc
import sys
import os
import tamperproofbroadcast
import blockchain
import paciofs
import module

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("paciofsserver")


class PacioFSServer(module.Module):
    def __init__(self, host="localhost", port=None):
        self.host = host
        if port == None:
            self.port = port_for.select_random()
        else:
            self.port = int(port)

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
            paciofs.PacioFS._Parser(),
            tamperproofbroadcast.TamperProofBroadcast._Parser(),
            blockchain.Blockchain._Parser(),
        ]
    )
    parser.add_argument("--logginglevel", default="INFO")
    args = parser.parse_args()
    logging.getLogger().setLevel(args.logginglevel)

    b = blockchain.Blockchain._Init(args)
    bc = tamperproofbroadcast.TamperProofBroadcast._Init(args)
    pfs = paciofs.PacioFS._Init(args)
    pfss = PacioFSServer._Init(args)

    bc._register_southbound(b)
    bc._register_northbound(pfs)
    pfs._register_southbound(bc)
    pfss._register_southbound(pfs)

    b._create()
    b._start()
    bc._create()
    bc._start()
    pfs._create()
    pfs._start()
    pfss._create()
    pfss._start()
