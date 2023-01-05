from typing import List
from typing import TYPE_CHECKING
import datetime
from aiogram import types
from..chain_model import ChainModel
from .base import BaseStorage

if TYPE_CHECKING:
    import aioredis

try:
    import ujson as json
except ImportError:
    import json


class RedisStorage(BaseStorage):
    async def __init__(self, connection: "aioredis.Redis", prefix: str, ttl: int):
        self._connection = connection
        self._prefix = prefix
        self._ttl = ttl

    async def add_message(self, description: ChainModel) -> bool:
        try:
            await self._connection.set(
            name= datetime.datetime.strftime(datetime.datetime.now()),
            value=description.json()
            )
            return True
        except Exception as e:
            return False


    async def get_all_chain(self) -> List[ChainModel]| List:
        try:

            keys = await self._connection.keys()
            chain = [ChainModel.parse_obj(await self._connection.get(key)) for key in keys]
            return chain
        except Exception as e:
            return []


    async def delete_all(self) -> bool:
        try:

            keys = await self._connection.keys()
            chain = [await self._connection.delete(key) for key in keys]
            return True
        except Exception as e:
            return False
