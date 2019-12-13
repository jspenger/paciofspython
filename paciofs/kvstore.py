class KVStore(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(KVStore, self).__setitem__(key, [])
        self[key].append(value)
