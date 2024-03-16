from pydantic import BaseModel


class DiarizedSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float


class InputData(BaseModel):
    order_id: int
    data_path: str


class Order(BaseModel):
    order_id: int
    file_path: str


class ConvertData(BaseModel):
    value: Order
    headers: dict
