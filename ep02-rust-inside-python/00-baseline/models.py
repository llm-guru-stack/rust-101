from datetime import datetime

from pydantic import BaseModel   # v1


class Doc(BaseModel):
    id: str
    title: str
    text: str
    source: str
    url: str
    author: str
    created_at: datetime
    tags: list[str]
    acl: list[str]


class Batch(BaseModel):
    docs: list[Doc]
