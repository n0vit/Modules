from abc import abstractmethod, ABC
from typing import List
from ..model import CategoryModel



class BaseStorage(ABC):

    @abstractmethod
    async def get_category(self,doc_id: str) -> CategoryModel| None:
        raise NotImplementedError

    @abstractmethod
    async def get_subcategories(self,doc_id: str) -> List[CategoryModel]| None:
        raise NotImplementedError

    @abstractmethod
    async def get_branch_categories(self,doc_id: str) -> List[CategoryModel]| None:
        # use get childs clouthers
        raise NotImplementedError

    @abstractmethod
    async def get_all_categories() -> List[CategoryModel]| None:
        raise NotImplementedError

    @abstractmethod
    async def add_category(self,category: CategoryModel) -> CategoryModel:

        raise NotImplementedError

    @abstractmethod
    async def delete_category(self,doc_id: str, saveChilderns: bool = False) -> CategoryModel| None:
        """
        Don't forget delete this category from parent

        And delete all childs of this category if saveChildrens False

        Or Save and connect them to parent"""
        raise NotImplementedError

    @abstractmethod
    async def update_name_category(self,doc_id: str, name: str) -> CategoryModel:
        raise NotImplementedError

    @abstractmethod
    async def update_desciption_category(self,doc_id: str, description: str) -> CategoryModel:
        raise NotImplementedError

    @abstractmethod
    async def update_parent_id(self,doc_id: str, parent_id: str) -> CategoryModel:
        raise NotImplementedError

    @abstractmethod
    async def update_subcategories(self,doc_id: str, subcategories: List[str]) -> CategoryModel:
        raise NotImplementedError

    @abstractmethod
    async def update_extra_category(self,doc_id: str, extra: str) -> CategoryModel:
        raise NotImplementedError



