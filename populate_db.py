import logging
import csv
import sys
from sqlalchemy import or_, orm
from typing import List

from models.db import live_session, db_engine, Base, Restaurant, Diner, RestaurantTable, DietaryRestriction


logging.basicConfig(level=logging.INFO)
DIRECTORY = 'data/'
DINER_CSV_PATH = f'{DIRECTORY}diner_data.csv'
RESTAURANT_CSV_PATH = f'{DIRECTORY}restaurant_data.csv'
DIETARY_RESTRICTIONS = ["Nut-Free", "Paleo", "Gluten-Free", "Vegetarian", "Vegan"]


class PopulateData:
    def __init__(self, session: orm.session.Session) -> None:
        self.session = session

    def add_tables(self, restaurant: Restaurant, capacity: int, num_of_tables: int):
        for _ in range(num_of_tables):
            table = RestaurantTable(restaurant_id=restaurant.id, capacity=capacity)
            self.session.add(table)
            self.session.commit()

    @staticmethod
    def parse_restaurant_dietary_restrictions(dietary_restrictions: str):
        """Given a list of restaurant dietary_restrictions, return first names"""
        return [dietary_restriction.replace(" ", "-").split('-')[0] for dietary_restriction in dietary_restrictions.split(', ')]
        
    def fetch_dietary_restrictions(self, dietary_restrictions: str) -> List[str]:
        restrictions = self.parse_restaurant_dietary_restrictions(dietary_restrictions)
        query = self.session.query(DietaryRestriction)\
            .filter(or_(*[DietaryRestriction.name.like(f"{name}%") for name in restrictions]))\
                .order_by(DietaryRestriction.name.desc()).all()
        return query

    def populate_restaurants(self):
        try:
            with open(RESTAURANT_CSV_PATH, newline='') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=',')
                for row in reader:
                    endorsements = row["Endorsements"]
                    restaurant = Restaurant(
                        name=row["Name"],
                        dietary_restrictions=self.fetch_dietary_restrictions(endorsements) if endorsements else []
                    )
                    self.session.add(restaurant)
                    self.session.commit()

                    two_tables = int(row["No. of two-top tables"])
                    four_tables = int(row["No. of two-top tables"])
                    six_tables = int(row["No. of two-top tables"])

                    self.add_tables(restaurant=restaurant, capacity=2, num_of_tables=two_tables)
                    self.add_tables(restaurant=restaurant, capacity=4, num_of_tables=four_tables)
                    self.add_tables(restaurant=restaurant, capacity=6, num_of_tables=six_tables)

        except Exception as e:
            logging.warning(f"Could not create restaurant row: {e}")
                    
    def populate_diners(self):
        try:
            with open(DINER_CSV_PATH, newline='') as csvfile:
                diners = []
                reader = csv.DictReader(csvfile, delimiter=',')
                for row in reader:
                    longitude, latitude = row["Home Location"].split(",")
                    diner = Diner(
                        name=row['Name'], 
                        home_longitude=float(longitude),
                        home_latitude=float(latitude), 
                    )
                    diner.dietary_restrictions = self.fetch_dietary_restrictions(row["Dietary Restrictions"]) if row["Dietary Restrictions"] else []
                    diners.append(diner)
                self.session.add_all(diners)
                self.session.commit()

        except Exception as e:
            logging.warning(f"Could not create diner: {e}")

    def populate_dietary_restrictions(self):
        restrictions = [DietaryRestriction(name=restriction) for restriction in DIETARY_RESTRICTIONS]
        self.session.add_all(restrictions)
        self.session.commit()


def main() -> None:
    Base.metadata.drop_all(db_engine)

    logging.info("Creating DB")
    Base.metadata.create_all(db_engine, checkfirst=True)
    populate_data = PopulateData(session=live_session())
    
    populate_data.populate_dietary_restrictions()
    populate_data.populate_restaurants()
    populate_data.populate_diners()


if __name__ == '__main__':
    sys.exit(main())