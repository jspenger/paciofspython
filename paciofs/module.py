class Module():
    def _create(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass

    def _register_northbound(self, registrant):
        self.northbound = registrant

    def _register_southbound(self, registrant):
        self.southbound = registrant

    funcs = []
    def _handle_exit(self, exit_function):
        import atexit
        import signal
        atexit.register(exit_function)
        def _decorator(funcs):
            def __deco(signum, frame):
                for f in funcs:
                    f()
            return __deco
        Module.funcs.append(exit_function)
        signal.signal(signal.SIGTERM, _decorator(Module.funcs))
        signal.signal(signal.SIGINT, _decorator(Module.funcs))

    @classmethod
    def _Parser(cls):
        import argparse
        import inspect
        parser = argparse.ArgumentParser(add_help=False)
        group1 = parser.add_argument_group(cls.__name__)
        sig = inspect.signature(cls)
        for param in sig.parameters.values():
            default = param.default if param.default is not inspect.Parameter.empty else None
            group1.add_argument('--'.lower()+param.name, default=default, required=False)
        return parser

    @classmethod
    def _Init(cls, args):
        import inspect
        kwargs = {k: v for k, v in vars(args).items() if k in inspect.signature(cls).parameters}
        return cls(**kwargs)
