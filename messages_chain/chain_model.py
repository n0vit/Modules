from typing import List


from pydantic import BaseModel


class ChainModel(BaseModel):
    message_id: int|str| None
    data_id: List[str] | str | None
    is_media_group: bool = False
    content_type: str | List[str]
    text: str | None

