from fastapi import HTTPException
from api.requests import AvailableReservationRequest, ReservationRequest
from models.db import DietaryRestriction, Diner, Reservation, Restaurant, RestaurantTable
from src.reservation_manager import ReservationManager
from common.tests.db_setup import test_session
from typing import List
from datetime import datetime, timedelta
from common.tests.test_data import GenerateTestData
from populate_db import PopulateData
import pytest


class GenerateTestData:
    def __init__(self, session) -> None:
        self.session = session

    def fetch_object(self, obj):
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def add_test_diner(self, name: str, dietary_restrictions: List[str]):
        diner = Diner(name=name, dietary_restrictions=dietary_restrictions)
        return self.fetch_object(obj=diner)

    def add_test_restaurant(self, name: str, dietary_restrictions: List[str]):
        restaurant = Restaurant(name=name, dietary_restrictions=dietary_restrictions)
        return self.fetch_object(obj=restaurant)

    def add_table(self, capacity: int, restaurant_id: int):
        table = RestaurantTable(capacity=capacity, restaurant_id=restaurant_id)
        return self.fetch_object(obj=table)
    
    def add_reservation(self, table_id: int, diners: List[Diner], start_datetime: datetime):
        reservation = Reservation(table_id=table_id,
                                  diners=diners,
                                  start_datetime=start_datetime,
                                  end_datetime=start_datetime + timedelta(hours=2))
        return self.fetch_object(obj=reservation)
    
    def add_dietary_restrictions(self):
        populate_data = PopulateData(session=self.session)
        populate_data.populate_dietary_restrictions()


class TestReservationManager:
    def test__find_available_restaurant__one_diner_no_conflict(self, test_session):
        """Test one diner, one restaurant, no conditions"""
        test_data = GenerateTestData(session=test_session)
        self.reservation_manager = ReservationManager(session=test_session)
        diner = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        expected_restaurant = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        test_data.add_table(capacity=2, restaurant_id=expected_restaurant.id)

        reservation_request = ReservationRequest(start_time=datetime(2024, 8, 24, 19, 0, 0), diner_ids=[diner.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)

        assert len(restaurants) == 1
        assert restaurants[0] == expected_restaurant

    def test__find_reservation__exact_same_time(self, test_session):
        """Test one diner, one restaurant, reservation exists at time"""
        test_data = GenerateTestData(session=test_session)
        self.reservation_manager = ReservationManager(session=test_session)
        diner = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        restaurant = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table = test_data.add_table(capacity=2, restaurant_id=restaurant.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)
        test_data.add_reservation(table_id=table.id, diners=[diner], start_datetime=start_datetime)
        
        reservation_request = ReservationRequest(start_time=start_datetime, diner_ids=[diner.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)
        assert len(restaurants) == 0

    def test__find_reservation__has_time_overlap(self, test_session):
        """Test one diner, one restaurant, reservation exists at time"""
        test_data = GenerateTestData(session=test_session)
        self.reservation_manager = ReservationManager(session=test_session)
        diner = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        restaurant = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table = test_data.add_table(capacity=2, restaurant_id=restaurant.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)
        test_data.add_reservation(table_id=table.id, diners=[diner], start_datetime=datetime(2024, 8, 24, 17, 0, 0))
        
        reservation_request = ReservationRequest(start_time=start_datetime, diner_ids=[diner.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)
        assert len(restaurants) == 0


    def test__find_reservation__dietary_restrictions_not_covered(self, test_session):
        """Test one diner, one restaurant, dietary restrictions not covered"""
        test_data = GenerateTestData(session=test_session)
        test_data.add_dietary_restrictions()
        dietary_restriction = test_session.get(DietaryRestriction, 1)

        self.reservation_manager = ReservationManager(session=test_session)
        diner = test_data.add_test_diner(name="Guy1", dietary_restrictions=[dietary_restriction])
        restaurant = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table = test_data.add_table(capacity=2, restaurant_id=restaurant.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)
        test_data.add_reservation(table_id=table.id, diners=[diner], start_datetime=start_datetime)
        
        reservation_request = ReservationRequest(start_time=start_datetime, diner_ids=[diner.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)
        assert len(restaurants) == 0

    def test__find_reservation__dietary_restrictions_restaurant_covers(self, test_session):
        """Test one diner, one restaurant, dietary restrictions covers it"""
        test_data = GenerateTestData(session=test_session)
        test_data.add_dietary_restrictions()
        dietary_restriction = test_session.get(DietaryRestriction, 1)

        self.reservation_manager = ReservationManager(session=test_session)
        diner = test_data.add_test_diner(name="Guy1", dietary_restrictions=[dietary_restriction])
        expected_restaurant = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[dietary_restriction])
        table = test_data.add_table(capacity=2, restaurant_id=expected_restaurant.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)
        
        reservation_request = ReservationRequest(start_time=start_datetime, diner_ids=[diner.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)
        assert len(restaurants) == 1
        assert restaurants[0] == expected_restaurant

    def test__find_reservation__has_no_capacity(self, test_session):
        """Two diners, one restaurant, table with only one capacity"""
        test_data = GenerateTestData(session=test_session)
        test_data.add_dietary_restrictions()

        self.reservation_manager = ReservationManager(session=test_session)
        diner1 = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        diner2 = test_data.add_test_diner(name="Guy2", dietary_restrictions=[])
        expected_restaurant = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table = test_data.add_table(capacity=1, restaurant_id=expected_restaurant.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)
        
        reservation_request = ReservationRequest(start_time=start_datetime, diner_ids=[diner1.id, diner2.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)
        assert len(restaurants) == 0

    def test__find_reservation__two_restaurants(self, test_session):
        """Two diners, Two restaurants, one with dietary restriction match"""
        test_data = GenerateTestData(session=test_session)
        test_data.add_dietary_restrictions()
        dietary_restriction1 = test_session.get(DietaryRestriction, 1)
        dietary_restriction2 = test_session.get(DietaryRestriction, 2)

        self.reservation_manager = ReservationManager(session=test_session)
        diner1 = test_data.add_test_diner(name="Guy1", dietary_restrictions=[dietary_restriction1])
        diner2 = test_data.add_test_diner(name="Guy2", dietary_restrictions=[dietary_restriction2])

        expected_restaurant1 = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[dietary_restriction1, dietary_restriction2])
        table1 = test_data.add_table(capacity=2, restaurant_id=expected_restaurant1.id)

        expected_restaurant2 = test_data.add_test_restaurant(name="Rest2", dietary_restrictions=[dietary_restriction2])
        table2 = test_data.add_table(capacity=2, restaurant_id=expected_restaurant2.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)
        
        reservation_request = ReservationRequest(start_time=start_datetime, diner_ids=[diner1.id, diner2.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)
        assert len(restaurants) == 1
        assert restaurants[0] == expected_restaurant1

    def test__find_reservation__one_diner_already_booked(self, test_session):
        """Two diners, Two restaurants, one diner already booked"""
        test_data = GenerateTestData(session=test_session)

        self.reservation_manager = ReservationManager(session=test_session)
        diner1 = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        diner2 = test_data.add_test_diner(name="Guy2", dietary_restrictions=[])

        expected_restaurant1 = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table1 = test_data.add_table(capacity=2, restaurant_id=expected_restaurant1.id)

        expected_restaurant2 = test_data.add_test_restaurant(name="Rest2", dietary_restrictions=[])
        table2 = test_data.add_table(capacity=2, restaurant_id=expected_restaurant2.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)
        
        test_data.add_reservation(table_id=table1.id, diners=[diner1], start_datetime=start_datetime)

        reservation_request = ReservationRequest(start_time=start_datetime, diner_ids=[diner1.id, diner2.id])
        restaurants = self.reservation_manager.find_available_restaurant(reservation_request=reservation_request)
        assert len(restaurants) == 1

    def test__book_reservation__no_conflicts(self, test_session):
        """Book a table from a restaurant for one person"""
        test_data = GenerateTestData(session=test_session)
        diner1 = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        restaurant1 = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table = test_data.add_table(capacity=2, restaurant_id=restaurant1.id)

        available_reservation_request = AvailableReservationRequest(
            start_time=datetime(2024, 8, 24, 16, 0, 0),
            diner_ids=[diner1.id],
            restaurant_id=restaurant1.id
        )

        self.reservation_manager = ReservationManager(session=test_session)
        reservation = self.reservation_manager.book_reservation(available_reservation_request=available_reservation_request)

        assert reservation.start_datetime == datetime(2024, 8, 24, 16, 0, 0)
        assert reservation.end_datetime == datetime(2024, 8, 24, 16, 0, 0)  + timedelta(hours=2)
        assert reservation.table_id == table.id

    def test__book_reservation__with_reservation_time_overlap(self, test_session):
        """Book a table from a restaurant with a time overlap"""
        test_data = GenerateTestData(session=test_session)
        diner1 = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        restaurant1 = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table1 = test_data.add_table(capacity=2, restaurant_id=restaurant1.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)

        test_data.add_reservation(table_id=table1.id,
                                  diners=[diner1],
                                  start_datetime=start_datetime + timedelta(hours=1))
        
        available_reservation_request = AvailableReservationRequest(
            start_time=start_datetime,
            diner_ids=[diner1.id],
            restaurant_id=restaurant1.id
        )

        self.reservation_manager = ReservationManager(session=test_session)
        reservation = self.reservation_manager.book_reservation(available_reservation_request=available_reservation_request)
        assert reservation == None

    def test__delete_reservation(self, test_session):
        test_data = GenerateTestData(session=test_session)
        diner1 = test_data.add_test_diner(name="Guy1", dietary_restrictions=[])
        restaurant1 = test_data.add_test_restaurant(name="Rest1", dietary_restrictions=[])
        table1 = test_data.add_table(capacity=2, restaurant_id=restaurant1.id)
        start_datetime=datetime(2024, 8, 24, 16, 0, 0)

        reservation = test_data.add_reservation(table_id=table1.id, diners=[diner1], start_datetime=start_datetime)
        self.reservation_manager = ReservationManager(session=test_session)
        
        result = self.reservation_manager.delete_reservation(reservation_id=reservation.id)
        assert result == True

    def test__delete_reservation__reservation_does_not_exist(self, test_session):
        with pytest.raises(HTTPException):
            self.reservation_manager = ReservationManager(session=test_session)
            self.reservation_manager.delete_reservation(reservation_id=1)