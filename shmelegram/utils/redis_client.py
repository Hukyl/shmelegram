"""
This modules provides custom RedisClient
Defines following classes:
    - `RedisClient`
"""

from typing import NoReturn

from redis import Redis


class RedisClient(Redis):
    # pylint: disable=abstract-method

    """
    Custom Redis client.
    Every connection and disconnection flushes all db data.
    (See redis's `flushdb` command).
    """

    def __init__(self, *args, **kwargs) -> NoReturn:
        super().__init__(*args, **kwargs)
        self.flushdb(asynchronous=True)

    def close(self) -> NoReturn:
        """
        Overrides close function.
        Before close flushes database data asyncronosly.

        Returns:
            NoReturn
        """
        self.flushdb(asynchronous=True)
        super().close()
