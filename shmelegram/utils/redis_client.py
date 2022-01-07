from redis import Redis


class RedisClient(Redis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flushdb(asynchronous=True)

    def close(self):
        self.flushdb(asynchronous=True)
        super().close()