import asyncio
import aiohttp
import random


class LinearRequester:
    """asynchronized & linearized http requester"""

    def __init__(self, *args, sleep_range=(3, 5), **kwargs):
        self._lock = asyncio.Lock()

        self._session = None

        self._session_args = args
        self._session_kwargs = kwargs
        self._sleep_range = sleep_range

    async def __aenter__(self):
        await self._lock.acquire()
        await asyncio.sleep(random.randint(*self._sleep_range))
        self._session = aiohttp.ClientSession(
            *self._session_args, **self._session_kwargs)
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        await self._session.close()
        self._lock.release()
