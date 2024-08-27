from models.db import DietaryRestriction, Diner, Restaurant
from common.tests.db_setup import test_session
from populate_db import PopulateData
from typing import List
from datetime import datetime


class GenerateTestData:
    def generate_dietary_restrictions(self, test_session=test_session):
        PopulateData(session=self.test_session).populate_dietary_restrictions()

    def generate_diner(self, name: str, dietary_restrictions: List[str], test_session):
        result = test_session.add(Diner(name=name, dietary_restriction=dietary_restrictions))
        self.test_session.commit()
        return result

    def generate_restaurant(self, name: str, dietary_restrictions: List[str], test_session):
        restaurant = self.test_session.add(Restaurant(name=name, dietary_restriction=dietary_restrictions))
        self.test_session.commit()
        return restaurant