import asyncio
from aiogram import Dispatcher
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import errors

from aiogram import __version__ as AIOGRAM_VERSION

AIOGRAM_VERSION = int(AIOGRAM_VERSION[0])


if AIOGRAM_VERSION == 3:

    STORAGE = []

elif AIOGRAM_VERSION == 2:
    from aiogram.contrib.fsm_storage.memory import MemoryStorage as AiogramMemoryStorage

    MONGO_INSTALLED = False
    try:
        from motor import motor_asyncio

        from aiogram.contrib.fsm_storage.mongo import MongoStorage as AiogramMongoStorage

        from .storage.mongo import MongoStorage
    except ModuleNotFoundError:
        # ignore if motor is not installed
        pass
    else:
        MONGO_INSTALLED = True



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

    def __init__(self, host='localhost', port=27017, db_name='support', uri=None,
                 username=None, password=None, **kwargs):
        self._host = host
        self._port = port
        self._db_name: str = db_name
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
        return self._mongo.get_database(self._db_name)




class CategoryRepo:
    def __init__(self, storage: Dispatcher  | MongoConnection, storage_prefix:str| None, ttl: int = 2) -> None:
        self.storage= storage
        self.prefix = storage_prefix
        self.ttl = ttl

    def init(self) ->   MongoStorage :
        type_storage = type(self.storage)
        match type_storage.__name__:
            case 'Dispatcher':
                loop = asyncio.get_event_loop()

                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    return loop.run_until_complete(self._wrap_storage(self.storage.get_current().storage))

                else:
                    return loop.create_task(self._wrap_storage(self.storage.get_current().storage))

            case 'MongoConnection':
                return MongoStorage(self.storage.get_mongo())


    async def _wrap_storage(self, storage: AiogramMemoryStorage|AiogramMongoStorage) ->   MongoStorage | None:
        storage_type = type(storage)

        if MONGO_INSTALLED:
            if storage_type is AiogramMongoStorage:
                mongo: motor_asyncio.AsyncIOMotorDatabase = await storage.get_db()
                return MongoStorage(db=mongo)

        else:
            raise ValueError(f"{storage_type} is unsupported storage")
