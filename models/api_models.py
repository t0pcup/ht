from pydantic import BaseModel


class DiarizedSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float


class Order(BaseModel):
    order_id: int
    file_path: str


class ConvertData(BaseModel):
    value: Order
    headers: dict
