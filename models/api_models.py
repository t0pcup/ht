from typing import List
from pydantic import BaseModel


class DiarizedSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float


class OrderOut(BaseModel):
    order_id: int
    segments: List[DiarizedSegment]


class Order(BaseModel):
    order_id: int
    file_path: str


class ConvertData(BaseModel):
    value: Order
    headers: dict
