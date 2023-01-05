from enum import Enum
from aiogram import Dispatcher
from . import AIOGRAM_VERSION
from .storage.memory import MemoryStorage
from .storage.base import BaseStorage

if AIOGRAM_VERSION == 3:
    # Currently for aiogram3 MemoryStorage is used, because this version is still in development
    # It breaks backward compatibility by introducing new breaking changes

    # from aiogram.dispatcher.fsm.storage.base import BaseStorage as AiogramBaseStorage
    # from aiogram.dispatcher.fsm.storage.memory import MemoryStorage as AiogramMemoryStorage
    # try:
    #     import aioredis

    #     from aiogram.dispatcher.fsm.storage.redis import RedisStorage as AiogramRedisStorage

    #     from .storages.redis import RedisStorage
    # except ModuleNotFoundError:
    #     # ignore if aioredis is not installed
    #     pass

    STORAGE = []

elif AIOGRAM_VERSION == 2:
    from aiogram.contrib.fsm_storage.memory import MemoryStorage as AiogramMemoryStorage

    MONGO_INSTALLED = False
    REDIS_INSTALLED = False

    try:
        from motor import motor_asyncio

        from aiogram.contrib.fsm_storage.mongo import MongoStorage as AiogramMongoStorage

        from .storage.mongo import MongoStorage
    except ModuleNotFoundError:
        # ignore if motor is not installed
        pass
    else:
        MONGO_INSTALLED = True


    try:
        import aioredis

        from aiogram.contrib.fsm_storage.redis import (
            RedisStorage as AiogramRedisStorage,
            RedisStorage2 as AiogramRedis2Storage,
        )

        from .storage.redis import RedisStorage
    except ModuleNotFoundError:
        # ignore if aioredis is not installed
        pass
    else:
        REDIS_INSTALLED = True

class Storages(Enum):
    MONGO =  MongoStorage
    REDIS = RedisStorage
    MEMORY = MemoryStorage



class   ChainRepo(BaseStorage):
    """ General Repository


    Args:
        storage: You put Dispatcher from aiogram & Chain will use storage defined in aiogram  OR  put concret storage
    Example:

    """
    async def __init__(self, storage: Dispatcher | Storages, storage_prefix:str| None, ttl: int = 2) -> None:

        if type(storage) is Dispatcher:
            storage = storage.get_current().storage


        await self._wrap_storage(
                        storage, storage_prefix, ttl
                    )


    async def _wrap_storage(self, storage: AiogramMemoryStorage|AiogramMongoStorage|AiogramRedisStorage| AiogramRedis2Storage, prefix: str, ttl: int) -> MemoryStorage | MongoStorage | RedisStorage | None:
        storage_type = type(storage)

        if storage_type is AiogramMemoryStorage:
            return MemoryStorage(data=[])

        elif MONGO_INSTALLED:
            if storage_type is AiogramMongoStorage:
                mongo: motor_asyncio.AsyncIOMotorDatabase = await storage.get_db()
                return MongoStorage(db=mongo, prefix=prefix, ttl=ttl)

        elif REDIS_INSTALLED:
            if storage_type is AiogramRedisStorage:
                connection: aioredis.Connection = await storage.redis()
                return RedisStorage(connection=connection, prefix=prefix, ttl=ttl)

            elif storage_type is AiogramRedis2Storage:
                redis: aioredis.Redis = await storage.redis()
                return RedisStorage(connection=redis, prefix=prefix, ttl=ttl)

        else:
            raise ValueError(f"{storage_type} is unsupported storage")

    #     class ChainControlModel(Document, ChainModel):
    #         pass

    #         # Beanie uses Motor under the hood
    #     client = AsyncIOMotorClient(uri)
    #     client.get_io_loop = asyncio.get_running_loop
    #     logging.info(f"Chain Repo {client.server_info}")
    #     db = client[database]
    #     await ChainControlModel.init_model(db,True)
    #     self.db = ChainControlModel


    # async def add_descr(self, description: ChainModel) -> None:
    #     description = self.db.parse_obj(description.dict())
    #     await self.db.insert_one(description)

    # async def get_all_descr(self) -> List[ChainModel]:
    #     try:
    #         all = await self.db.all().to_list()
    #         all = [ChainModel.parse_obj(_) for _ in all]
    #         return all
    #     except Exception as e:
    #         print(e, "обработан неверно")

    # async def update_descr(self, new_data: ChainModel) -> None:
    #     descr = await self.db.all().to_list()
    #     data = descr[-1]
    #     data_id = data.data_id.append(new_data.data_id)
    #     content_type = data.content_type.append(new_data.content_type)
    #     if new_data.text:
    #         text = new_data.text
    #     else:
    #         text = data.text
    #     data = Set({"data_id": data_id, "content_type": content_type, "text": text})
    #     await descr[-1].update(data)

    # async def delete_all(self) -> None:
    #     await self.db.delete_all()
