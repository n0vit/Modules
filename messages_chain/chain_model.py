from typing import List


from pydantic import BaseModel


class ChainModel(BaseModel):
    data_id: List[str] | str | None
    is_media_group: bool = False
    content_type: str | List[str]
    text: str | None

