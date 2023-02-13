import asyncio
import logging
import threading
from typing import List
from typing import Literal
from typing import TYPE_CHECKING


from ..chain_model import ChainModel

from .base import BaseStorage

if TYPE_CHECKING:
    from motor import motor_asyncio

try:
    from pymongo.errors import OperationFailure
except ImportError:
    pass

try:
    import ujson as json
except ImportError:
    import json

Documents = Literal["MessageChain"]


class MongoStorage(BaseStorage):
    def __init__(self, client: "motor_asyncio.AsyncIOMotorClient", db_name,prefix: str, ttl: int):
        self._ttl = ttl
        self._collection: motor_asyncio.AsyncIOMotorCollection = client[db_name][prefix]

        loop = asyncio.get_event_loop()

        #  This happens when MongoDB driver is used as storage_driver argument
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            client.get_io_loop = asyncio.get_running_loop
            db = client[db_name]
            loop.run_until_complete(self._create_collection(db, prefix, ttl))
            loop.close()
        else:
            threading.Thread(target=self._tread_init,name=f'Message Chain {prefix} init',args=(client,db_name, prefix, ttl)).run()


    def _tread_init(self, client, db_name,prefix, ttl):
        loop = asyncio.new_event_loop()
        client.get_io_loop = asyncio.get_running_loop
        db = client[db_name]
        loop.run_until_complete(self._create_collection(db, prefix, ttl))
        loop.close()
        logging.debug('Message Chain inited')


    async def _create_collection(self, db: "motor_asyncio.AsyncIOMotorDatabase", prefix: str, ttl: int):
        try:
            if prefix not in await db.list_collection_names():
                await db.create_collection(prefix)

            if "expireAt" not in await self._list_index_names(db, prefix):
                await db[prefix].create_index("expireAt", expireAfterSeconds=ttl)

            elif ttl != self._ttl:
                self._ttl = ttl
                await db.command("collMod", prefix, index={ "keyPattern": { "expireAt": 1 }, "expireAfterSeconds": ttl })

        except OperationFailure:
            pass

    async def _list_index_names(self, db: "motor_asyncio.AsyncIOMotorDatabase", prefix: str) -> List[str]:
        names = []

        async for index in db[prefix].list_indexes():
            index = json.loads(json.dumps(index, default=lambda item: getattr(item, "__dict__", str(item))))
            name = list(index["key"].keys())[0]

            if name == "expireAt":
                self._ttl = index["expireAfterSeconds"]

            names.append(name)

        return names

    async def add_message(self, description: ChainModel) -> None:
        try:
            response =  self._collection.insert_one(description.dict())
            return response
        except Exception as e:
            logging.error(e)

    async def get_all_chain(self) -> List[ChainModel]:
        try:
            cursor =self._collection.find({})
            return await cursor.to_list(length=50)
        except Exception as e:
            logging.error(e)


    async def delete_all(self) -> None:
        await self._collection.delete_many({})
