import asyncio
import logging
from typing import List
from typing import TYPE_CHECKING
import itertools
from ..model import CategoryModel
from .base import BaseStorage

if TYPE_CHECKING:
    from motor import motor_asyncio
    from beanie import Document, init_beanie
    from beanie.operators import  Set





class MongoStorage(BaseStorage):
    def __init__(self, db: "motor_asyncio.AsyncIOMotorDatabase"):
        class MongoCategoryModel(Document,CategoryModel):
            pass
        self.document= MongoCategoryModel
        loop = asyncio.get_event_loop()

        #  This happens when MongoDB driver is used as storage_driver argument
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(init_beanie(database=db, document_models=[MongoCategoryModel]))
            loop.close()
        else:
            loop.create_task(init_beanie(database=db, document_models=[MongoCategoryModel]))


    async def get_category(self,doc_id: str) -> CategoryModel | None:
        return await  self.document.get(doc_id)


    async def get_subcategories(self,doc_id: str) -> List[CategoryModel] | None:
        try:
            category = await self.get_category(doc_id)
            if category:
                return await self.document.find_many([category.subcategories])
            return None
        except Exception as e:
            logging.error(e)
            return None

    async def get_branch_categories(self,doc_id: str) -> List[CategoryModel] | None:
        try:
            categories = []
            category = await self.document.get(doc_id)
            if category:
                subcats = await self.get_subcategories(doc_id)
                if subcats:
                    categories.extend(subcats)
                    for sub in subcats:
                        cats = await self.get_branch_categories(sub.id)
                        categories.append(cats)
                else:
                    return categories
        except Exception as e:
            logging.error(e)
            return None

    async def get_all_categories(self) -> List[CategoryModel] | None:
        try:
            root_categories = await self.document.find({"id": "root"}).to_list()
            all_categories = []
            for branch in root_categories:
                all_categories.append(self.get_branch_categories(branch.id))
        except Exception as e:
            logging.error(e)
            return None

    async def add_category(self, category: CategoryModel) -> CategoryModel | None:
        try:
            new_category =  await self.document.insert_one(category)
            if category.parent_id != 'root':
                parent  = await self.document.get(category.parent_id)
                parent.subcategories.append(category.id)
                await self.update_subcategories(parent.id, parent.subcategories)
            return new_category
        except Exception as e:
            logging.error(e)
            return None


    async def delete_category(self, doc_id: str, saveChilderns: bool = False) ->  None:
        try:
            category = await self.get_category(doc_id)
            if category:
                if  not category.subcategories:
                    await self.document.delete(doc_id)
                    return

                if saveChilderns:
                    if category.parent_id == 'root':
                        for cat in category.subcategories:
                            self.update_parent_id(cat, 'root')
                    else:
                        parent = await self.get_category(category.parent_id)
                        parent.subcategories.pop(parent.subcategories.index(category.id))
                        parent.subcategories.extend(category.subcategories)
                        await self.update_subcategories(parent.subcategories,parent.id)
                else:
                    if category.parent_id != 'root':
                        parent = await self.get_category(category.parent_id)
                        parent.subcategories.pop(parent.subcategories.index(category.id))
                        await self.update_subcategories(parent.subcategories,parent.id)

                    branch = self.get_branch_categories(doc_id)
                    deletly_categories: List[CategoryModel] = list(itertools.chain(*branch))
                    deletly_categories.append(category)
                    for _ in deletly_categories:
                        await self.document.delete(_.id)

        except Exception as e:
            logging.error(e)
            return None


    async def update_name_category(self,doc_id: str, name: str) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set(category.name, name)
            await category.update(new_data)
            category.name = name
            return category
        except Exception as e:
            logging.error(e)
            return None


    async def update_desciption_category(self, doc_id: str, description: str) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set(category.description, description)
            await category.update(new_data)
            category.description = description
            return category
        except Exception as e:
            logging.error(e)
            return None



    async def update_parent_id(self, doc_id: str, parent_id: str) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set(category.parent_id, parent_id)
            await category.update(new_data)
            category.parent_id = parent_id
            return category
        except Exception as e:
            logging.error(e)
            return None



    async def update_subcategories(self, doc_id: str, subcategories: List[str]) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            category.subcategories.extend(subcategories)
            new_data = Set(category.subcategories,  category.subcategories)
            await category.update(new_data)
            category.subcategories = subcategories
            return category
        except Exception as e:
            logging.error(e)
            return None

    async def update_extra_category(self,doc_id: str, extra: str) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set(category.extra, extra)
            await category.update(new_data)
            category.extra = extra
            return category
        except Exception as e:
            logging.error(e)
            return None
