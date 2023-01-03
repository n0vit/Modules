from typing import List

from beanie.odm.operators.update.general import Set
from beanie import Document
from ...handlers.errors.errors import Errors
from .chain_model import  ChainModel


class ChainRepo:
    def __init__(self,document) -> None:

        class ChainControlModel(Document, ChainModel):
            ...

        self.db = ChainControlModel
        document.doc = self.db

    async def add_descr(self, description: ChainModel) -> None:
        description = self.db.parse_obj(description.dict())
        await self.db.insert_one(description)

    async def get_all_descr(self) -> List[ChainModel]:
        try:
            all = await self.db.all().to_list()
            all = [ChainModel.parse_obj(_) for _ in all]
            return all
        except Errors.HandlerError as e:
            print(e, "обработан неверно")

    async def update_descr(self, new_data: ChainModel) -> None:
        descr = await self.db.all().to_list()
        data = descr[-1]
        data_id = data.data_id.append(new_data.data_id)
        content_type = data.content_type.append(new_data.content_type)
        if new_data.text:
            text = new_data.text
        else:
            text = data.text
        data = Set({"data_id": data_id, "content_type": content_type, "text": text})
        await descr[-1].update(data)

    async def delete_all(self) -> None:
        await self.db.delete_all()
