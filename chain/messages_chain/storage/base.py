from abc import abstractmethod, ABC
from typing import List
from ..chain_model import ChainModel


class BaseStorage(ABC):


    @abstractmethod
    async def add_message(self, description: ChainModel) -> None:
        pass

    @abstractmethod
    async def get_all_chain(self) -> List[ChainModel]:
        pass


    @abstractmethod
    async def delete_all(self) -> None:
        pass
