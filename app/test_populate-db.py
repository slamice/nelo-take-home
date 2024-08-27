from typing import List
from app.models.db import DietaryRestriction
from populate_db import PopulateData
from common.tests.db_setup import test_session



class TestPopulateDatabase:
    def test__parse_restauraunt_dietary_restrictions__returns_first_names(self, test_session):
        populate_data = PopulateData(session=test_session)
        parsed_dietary_restrictions = populate_data.parse_restaurant_dietary_restrictions("Vegan-Friendly, Vegetarian-Friendly, Gluten Free Options")
        assert ["Vegan", "Vegetarian", "Gluten"] == parsed_dietary_restrictions

    def test__fetch_dietary_restrictions__returns_correct_restriction_objects_from_first_names(self, test_session):
        populate_data = PopulateData(session=test_session)
        populate_data.populate_dietary_restrictions()

        parsed_dietary_restrictions = populate_data.fetch_dietary_restrictions("Paleo, Gluten")
        expected_result = test_session.query(DietaryRestriction)\
            .filter(DietaryRestriction.name.in_(["Paleo", "Gluten-Free"])).order_by(DietaryRestriction.name.desc()).all()
        
        assert len(parsed_dietary_restrictions) == 2
        assert parsed_dietary_restrictions[0] == expected_result[0]
        assert parsed_dietary_restrictions[1] == expected_result[1]
