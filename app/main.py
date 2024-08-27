from fastapi import FastAPI, status, HTTPException

from .models.db import live_session
from .api.requests import ReservationRequest, AvailableReservationRequest
from .api.responses import RestaurantResponse, ReservationResponse
from .reservations.reservation_manager import ReservationManager
from typing import List


app = FastAPI()


@app.post("/find_reservation/", status_code=status.HTTP_200_OK)
def find_available_tables(request: ReservationRequest):
    """
    An endpoint to find restaurants with an available table for a group of users at a specific time.
    Thought about it being a GET since we are fetching, and we can switch to that if needed.
    """
    try:
        results = ReservationManager(session=live_session()).find_available_restaurant(request)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not find any tables: {e}")
    
    return [RestaurantResponse(**{"id": result.id, "restaurant_name": result.name}) for result in results]


@app.post("/book_restaurant/", status_code=status.HTTP_201_CREATED)
def book_table(available_reservation_request: AvailableReservationRequest):
    """
    Endpoint that creates a reservation for a group of users. This will always be called
    after the search endpoint above.
    """
    reservation = ReservationManager(session=live_session()).book_reservation(available_reservation_request=available_reservation_request)

    if not reservation:
        raise HTTPException(status_code=404, detail="No available table found")
    
    return ReservationResponse(**{
        "id":reservation.id,
        "restaurant_id": available_reservation_request.restaurant_id,
        "diner_ids": available_reservation_request.diner_ids
    })


@app.delete("/reservation/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(reservation_id):
    """Deletes a reservation by id"""
    ReservationManager(session=live_session()).delete_reservation(reservation_id=reservation_id)
    return {"ok": True}