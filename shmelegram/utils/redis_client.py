"""
This modules provides custom RedisClient
Defines following classes:
    - `RedisClient`
"""

from typing import NoReturn, Any

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


class FakeRedisClient:
    """
    Fake Redis Client. Values are converted and stored as strings.
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=unused-argument
        self._data = {}

    def get(self, key: str) -> str:
        """
        Get value by key. Since values converted into strings, returns string.

        Args:
            key (str)

        Raises:
            KeyError: if no such key found

        Returns:
            str
        """
        return self._data[key]

    def set(self, key: str, value: Any) -> NoReturn:
        """
        Set key-value pair. Value is converted and stored as string.

        Args:
            key (str)
            value (Any)

        Returns:
            NoReturn
        """
        self._data[key] = str(value)

    def delete(self, *args: str) -> NoReturn:
        """
        Delete all values by given keys.

        Raises:
            KeyError: if at least one key is not present

        Returns:
            NoReturn
        """
        for key in args:
            del self._data[key]
