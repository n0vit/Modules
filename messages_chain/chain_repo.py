import asyncio
from enum import Enum
import typing
from aiogram import Dispatcher
from aioredis import Redis
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import errors
from .storage.memory import MemoryStorage


from aiogram import __version__ as AIOGRAM_VERSION

AIOGRAM_VERSION = int(AIOGRAM_VERSION[0])


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



class RedisConnection:

    def __init__(
            self,
            host: str = "localhost",
            port: int = 6379,
            db: typing.Optional[int] = None,
            password: typing.Optional[str] = None,
            ssl: typing.Optional[bool] = None,
            pool_size: int = 10,
            loop: typing.Optional[asyncio.AbstractEventLoop] = None,
            prefix: str = "fsm",
            state_ttl: typing.Optional[int] = None,
            data_ttl: typing.Optional[int] = None,
            bucket_ttl: typing.Optional[int] = None,
            **kwargs,
    ):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._pool_size = pool_size
        self._kwargs = kwargs
        self._prefix = (prefix,)

        self._state_ttl = state_ttl
        self._data_ttl = data_ttl
        self._bucket_ttl = bucket_ttl

        self._redis: typing.Optional["aioredis.Redis"]
        self._connection_lock = asyncio.Lock()

    async def get_redis(self) -> Redis:
        async with self._connection_lock:  # to prevent race
            if self._redis is None:
                self._redis = aioredis.Redis(
                    host=self._host,
                    port=self._port,
                    db=self._db,
                    password=self._password,
                    ssl=self._ssl,
                    max_connections=self._pool_size,
                    decode_responses=True,
                    **self._kwargs,
                )
        return self._redis


class MongoConnection:
    """
    MongoConnection

    Usage:

    .. code-block:: python3

        storage = MongoStorage(host='localhost', port=27017, db_name='aiogram_fsm')
        dp = Dispatcher(bot, storage=storage)

    And need to close Mongo client connections when shutdown

    .. code-block:: python3

        await dp.storage.close()
        await dp.storage.wait_closed()
    """

    def __init__(self, host='localhost', port=27017, db_name='chain',collection_name='message_chain', uri=None,
                 username=None, password=None, **kwargs):
        self._host = host
        self._port = port
        self._db_name: str = db_name
        self.prefix = collection_name
        self._uri = uri
        self._username = username
        self._password = password
        self._kwargs = kwargs  # custom client options like SSL configuration, etc.

        if self._uri:
            try:
                self._mongo = AsyncIOMotorClient(self._uri, **self._kwargs)
            except errors.ConfigurationError as e:
                if "query() got an unexpected keyword argument 'lifetime'" in e.args[0]:
                    import logging
                    logger = logging.getLogger("aiogram")
                    logger.warning("Run `pip install dnspython==1.16.0` in order to fix ConfigurationError. More information: https://github.com/mongodb/mongo-python-driver/pull/423#issuecomment-528998245")
                raise e


        uri = 'mongodb://'

        # set username + password
        if self._username and self._password:
            uri += f'{self._username}:{self._password}@'

        # set host and port (optional)
        uri += f'{self._host}:{self._port}' if self._host else f'localhost:{self._port}'

        # define and return client
        self._mongo = AsyncIOMotorClient(uri)


    def get_mongo(self):
        return self._mongo, self._db_name



class MemoryConnection:
    pass



class ChainRepo:
    def __init__(self, storage:  MemoryConnection| RedisConnection | MongoConnection, storage_prefix:str| None, ttl: int = 2) -> None:
        self.storage= storage
        self.prefix = storage_prefix
        self.ttl = ttl

    def init(self) -> MemoryStorage | MongoStorage | RedisStorage:
        type_storage = type(self.storage)
        match type_storage.__name__:
            case 'MongoConnection':
                return MongoStorage(*self.storage.get_mongo(), self.prefix, ttl=self.ttl)

            case  'RedisConnection':
                return RedisStorage(self.storage.get_redis(), self.prefix, ttl=self.ttl)

            case 'MemoryConnection':
                return MemoryStorage(data=[])
                ...
