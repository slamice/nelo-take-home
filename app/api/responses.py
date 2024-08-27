from typing import List
from pydantic import BaseModel


class RestaurantResponse(BaseModel):
    id: int
    restaurant_name: str

class ReservationResponse(BaseModel):
    id: int
    restaurant_id: int
    diner_ids: List[int]