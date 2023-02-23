from __future__ import annotations
import asyncio
import logging
from typing import List
import itertools
from ..model import CategoryModel
from .base import BaseStorage
from motor import motor_asyncio
from beanie import Document, init_beanie, Link
from beanie.operators import Set
import threading


class MongoStorage(BaseStorage):
    def __init__(self, client: "motor_asyncio.AsyncIOMotorClient", db_name):
        class MongoCategoryModel(Document, CategoryModel):
            pass

        self.document = MongoCategoryModel
        loop = asyncio.get_event_loop()

        #  This happens when MongoDB driver is used as storage_driver argument
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            db = client.get_database(db_name)
            loop.run_until_complete(
                init_beanie(database=db, document_models=[MongoCategoryModel])
            )
            logging.debug("Category Repo inited")
            loop.close()
        else:
            threading.Thread(
                target=self._tread_init,
                name="Category Repo init",
                args=(client, db_name, MongoCategoryModel),
            ).start()

            # self.task = loop.create_task(self.init( db, MongoCategoryModel))

    @staticmethod
    def _tread_init(client, db_name, doc):
        loop = asyncio.new_event_loop()
        client.get_io_loop = asyncio.get_running_loop
        db = client.get_database(db_name)
        loop.run_until_complete(init_beanie(database=db, document_models=[doc]))
        logging.debug("Category Repo inited")

    async def get_category(self, doc_id: str) -> CategoryModel | None:
        doc = await self.document.get(doc_id)
        if doc.subcategories:
            doc.subcategories = [CategoryModel.parse_obj(_) for _ in doc.subcategories]
        return doc

    async def get_main_category(self) -> List[CategoryModel]:
        return await self.document.find(self.document.parent_id == "root").to_list()

    async def get_subcategories(self, doc_id: str) -> List[CategoryModel] | None:
        try:
            return await self.document.find(self.document.parent_id == doc_id).to_list()
        except Exception as e:
            logging.error(e)
            return None

    async def get_branch_categories(
        self, model: CategoryModel, delete: bool = False
    ) -> List[CategoryModel] | None:
        try:
            categories: List[CategoryModel] = [model]

            async def get_subs(cat: CategoryModel):
                subcats = await self.get_subcategories(str(cat.id))
                if subcats:
                    categories.extend(subcats)
                index = categories.index(cat) + 1
                if index == len(categories):
                    return
                await get_subs(categories[index])

            await get_subs(categories[0])
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
            new_category = await self.document.insert_one(
                self.document.parse_obj(category.dict(exclude={"id"}))
            )
            if category.parent_id != "root":
                parent = await self.document.get(category.parent_id)
                parent.subcategories.append(category.id)
            return new_category
        except Exception as e:
            logging.error(e)
            return None

    async def delete_category(self, doc_id: str, saveChilderns: bool = False) -> None:
        try:
            category = await self.get_category(doc_id)
            if category:
                subs = await self.get_subcategories(doc_id)
                if not subs:
                    await self.document.delete(category)
                    return

                if saveChilderns:
                    [
                        await self.update_parent_id(cat.id, category.parent_id)
                        for cat in subs
                    ]

                else:
                    branch = await self.get_branch_categories(category)
                    for _ in branch:
                        await _.delete()

        except Exception as e:
            logging.error(e)
            return None

    async def update_name_category(self, doc_id: str, name: str) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set({"name": name})
            await category.update(new_data)
            category.name = name
            return category
        except Exception as e:
            logging.error(e)
            return None

    async def update_desciption_category(
        self, doc_id: str, description: str
    ) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set({"description": description})
            await category.update(new_data)
            category.description = description
            return category
        except Exception as e:
            logging.error(e)
            return None

    async def update_parent_id(self, doc_id: str, parent_id: str) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set({"parent_id": parent_id})
            await category.update(new_data)
            category.parent_id = parent_id
            return category
        except Exception as e:
            logging.error(e)
            return None

    async def replace_subcategories(
        self, doc_id: str, subcategories: List[CategoryModel]
    ) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            for sub in subcategories:
                sub.id = str(sub.id)
            new_data = Set({"subcategories": subcategories})
            await category.update(new_data)
            category.subcategories = subcategories
            return category
        except Exception as e:
            logging.error(e)
            return None

    async def update_subcategories(
        self, doc_id: str, subcategories: List[CategoryModel]
    ) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            category.subcategories.extend(subcategories)
            new_data = Set({"subcategories": category.subcategories})
            await category.update(new_data)
            category.subcategories = subcategories
            return category
        except Exception as e:
            logging.error(e)
            return None

    async def update_extra_category(self, doc_id: str, extra: str) -> CategoryModel:
        try:
            category = await self.document.get(doc_id)
            new_data = Set({"extra": extra})
            await category.update(new_data)
            category.extra = extra
            return category
        except Exception as e:
            logging.error(e)
            return None
