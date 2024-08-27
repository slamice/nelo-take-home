from datetime import datetime
from typing import List
from pydantic import BaseModel


class ReservationRequest(BaseModel):
    start_time: datetime
    diner_ids: List[int]


class AvailableReservationRequest(ReservationRequest):
    restaurant_id: int

