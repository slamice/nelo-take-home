from fastapi import HTTPException
from ..app.api.requests import AvailableReservationRequest, ReservationRequest
from ..models.db import DietaryRestriction, Diner, Reservation, Restaurant, RestaurantTable, diner_dietary_restriction_association, restaurant_dietary_restriction_association
from sqlalchemy.orm.session import Session
from datetime import timedelta
from typing import List
from sqlalchemy import and_, asc, exists
import logging

logging.basicConfig(level=logging.INFO)
RESERVATION_DURATION = 2


class ReservationManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_available_restaurant(self, reservation_request: ReservationRequest) -> List[Restaurant]:
        """
        Params:
            given a available_reservation_request (diners, restaurant_id and start_datetime)
        Returns:
            Available Restaurants
        """
        diner_ids = reservation_request.diner_ids
        capacity = len(diner_ids)
        start_datetime = reservation_request.start_time
        end_datetime = start_datetime + timedelta(hours=RESERVATION_DURATION)

        logging.info(f"Find restauarants for diners {diner_ids}")
        # Ignore restaurants with conflicting reservations
        conflicting_restaurants = self.session.query(Restaurant.id).join(RestaurantTable).join(Reservation).filter(
            and_(Reservation.start_datetime < end_datetime, Reservation.end_datetime > start_datetime)
        ).distinct().all()
        conflicting_restaurant_ids = [row.id for row in conflicting_restaurants]

        # Filter diner restrictions
        diner_dietary_restrictions = self.session.query(DietaryRestriction.id).join(diner_dietary_restriction_association)\
            .filter(diner_dietary_restriction_association.c.diner_id.in_(diner_ids)).all()
        diner_dietary_restriction_ids = [row.id for row in diner_dietary_restrictions]
            
        query = self.session.query(Restaurant).join(RestaurantTable).filter(
            and_(
                RestaurantTable.capacity >= capacity,
                Restaurant.id.notin_(conflicting_restaurant_ids),
                *[exists().where(
                    and_(
                        restaurant_dietary_restriction_association.c.restaurant_id == Restaurant.id,
                        restaurant_dietary_restriction_association.c.dietary_restriction_id == restriction_id
                    )
                ) for restriction_id in diner_dietary_restriction_ids]
            )
            ).distinct()

        return query.all()


    def book_reservation(self, available_reservation_request: AvailableReservationRequest) -> Reservation:
        """
        Params:
            given a available_reservation_request (diners, restaurant_id and start_datetime)
        Returns:
            Reservation
        """
        # Get reserved tables to ignore
        restaurant_id = available_reservation_request.restaurant_id 
        diner_ids = available_reservation_request.diner_ids
        capacity = len(diner_ids)
        start_datetime = available_reservation_request.start_time
        end_datetime = start_datetime + timedelta(hours=RESERVATION_DURATION)
        
        logging.info(f"Booking a reservation for diners {diner_ids} with restaurant {restaurant_id}")
        reserved_tables = self.session.query(RestaurantTable.id).join(Reservation).filter(
                and_(
                    Reservation.table_id == RestaurantTable.id,
                    Reservation.start_datetime < end_datetime,
                    Reservation.end_datetime > start_datetime
                )
            )
        reserved_table_ids = [table.id for table in reserved_tables]

        available_table = self.session.query(RestaurantTable).filter(
            RestaurantTable.restaurant_id == restaurant_id,
            RestaurantTable.capacity >= capacity,
            RestaurantTable.id.notin_(reserved_table_ids)
        ).order_by(
            asc(RestaurantTable.capacity)
        ).first()

        if not available_table:
            logging.warning(f"Didnt find a table for Restaurant {restaurant_id}")
            return None

        diners = self.session.query(Diner).filter(Diner.id.in_(diner_ids)).all()
        available_reservation = Reservation(
            table_id=available_table.id,
            start_datetime=start_datetime,
            end_datetime = end_datetime,
            diners=diners
        )

        logging.warning(f"Booking table {available_table.id} with reservation {available_reservation.id}")
        self.session.add(available_reservation)
        self.session.commit()
        self.session.refresh(available_reservation)
        return available_reservation

    def delete_reservation(self, reservation_id: int) -> bool:
        """
        Params:
            reservation_id for a Reservation to delete
        Returns:
            Deletes True if successfuly deleted
        """
        
        reservation = self.session.get(Reservation, reservation_id)
        if not reservation:
            logging.warning(f"Could not find reservation for id {id}")
            raise HTTPException(status_code=400, detail="Reservation not found")
        
        self.session.delete(reservation)
        self.session.commit()

        logging.warning(f"Deleted reservation {reservation.id}")
        return True
