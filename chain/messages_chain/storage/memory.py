from typing import List, Dict

from aiogram import types

from Modules.messages_chain.chain_model import ChainModel

from .base import BaseStorage


class MemoryStorage(BaseStorage):
    def __init__(self, data: List):
        self._data = data

    async def add_message(self, description: ChainModel) -> None:

        self._data.append(description.dict())

    async def get_all_chain(self) -> List[ChainModel]:
        return [ChainModel.parse_obj(_) for _ in self._data]


    async def delete_all(self) -> None:
        self._data.clear()
