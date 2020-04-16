import logging.config
import subprocess
import threading
import binascii
import argparse
import logging
import inspect
import pickle
import atexit
import signal
import os

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
logger = logging.getLogger("module")


class Module:
    def __init__(self):
        self.northbound = {}
        self.southbound = {}

    def _create(self):
        pass

    def _uncreate(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass

    def _register_northbound(self, registrant, name=None):
        if name is not None:
            self.northbound[name] = registrant
        else:
            self.northbound = registrant

    def _register_southbound(self, registrant, name=None):
        if name is not None:
            self.southbound[name] = registrant
        else:
            self.southbound = registrant

    funcs = []

    def _handle_exit(self, exit_function):

        atexit.register(exit_function)

        def _decorator(funcs):
            def __deco(signum=None, frame=None):
                for f in funcs:
                    f()

            return __deco

        Module.funcs.append(exit_function)
        signal.signal(signal.SIGTERM, _decorator(Module.funcs))
        signal.signal(signal.SIGINT, _decorator(Module.funcs))

    def _execute_command(self, command, daemon=False, streaming=False):
        try:
            logger.debug("executing command: %s" % command)
            if daemon == True:

                def f():
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    _, _ = process.communicate()
                    if process.returncode != 0:
                        raise

                threading.Thread(target=f, daemon=True).start()
                return None
            else:
                if streaming == True:
                    result = subprocess.run(command, shell=True)
                    return result.stdout
                else:
                    result = subprocess.run(
                        command, shell=True, capture_output=True, check=True
                    )
                    return result.stdout
        except Exception as e:
            logger.error("error: %s" % e)
            raise e

    def _pack(self, message):
        return binascii.hexlify(pickle.dumps(message)).decode()

    def _unpack(self, payload):
        return pickle.loads(binascii.unhexlify(payload))

    @classmethod
    def _Parser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        group1 = parser.add_argument_group(cls.__name__)
        sig = inspect.signature(cls)
        for param in sig.parameters.values():
            default = (
                param.default if param.default is not inspect.Parameter.empty else None
            )
            group1.add_argument(
                "--" + cls.__name__.lower() + "-" + param.name,
                default=default,
                required=False,
            )
        return parser

    @classmethod
    def _Init(cls, args):
        prefix = cls.__name__.lower() + "_"
        kwargs = {
            k[len(prefix) :]: v
            for k, v in vars(args).items()
            if k.startswith(prefix)
            and k[len(prefix) :] in inspect.signature(cls).parameters
        }
        return cls(**kwargs)
