import uuid
from typing import List

from pydantic import BaseModel


UNKNOWN = uuid.UUID("99999999-9999-9999-9999-999999999999")


# class Page(BaseModel):
#     page_id: uuid.UUID
#     page_type_id: uuid.UUID = UNKNOWN
#     confidence: float = 0.0

class Text(BaseModel):
    text: str
    start: float
    end: float


class Word(Text):
    score: float


class DiarizedSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float
    # words: List[Word]


class InputData(BaseModel):
    order_id: int
    data_path: str
