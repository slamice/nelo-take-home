from sqlalchemy import Column, ForeignKey, Integer, Float, Sequence, String, Table, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base, sessionmaker


db_engine = create_engine('sqlite:///booking-system.db', echo = True)
Base = declarative_base()

def live_session():
    Session = sessionmaker(bind=db_engine, future=True)
    session = Session()
    return session


# Association Tables
diner_dietary_restriction_association = Table(
    'diner_dietary_restriction', Base.metadata,
    Column('diner_id', Integer, ForeignKey('diners.id')),
    Column('dietary_restriction_id', Integer, ForeignKey('dietary_restrictions.id'))
)

restaurant_dietary_restriction_association = Table(
    'restaurant_dietary_restriction', Base.metadata,
    Column('restaurant_id', Integer, ForeignKey('restaurants.id')),
    Column('dietary_restriction_id', Integer, ForeignKey('dietary_restrictions.id'))
)

diner_reservation_association = Table(
    'diner_reservation', Base.metadata,
    Column('diner_id', Integer, ForeignKey('diners.id')),
    Column('reservation_id', Integer, ForeignKey('reservations.id'))
)

class Diner(Base):
    __tablename__ = 'diners'
    id = Column(Integer, Sequence('diner_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    home_latitude = Column(Float(150), nullable=True)
    home_longitude = Column(Float(50), nullable=True)
    dietary_restrictions = relationship(
        'DietaryRestriction',
        secondary=diner_dietary_restriction_association,
        back_populates='diners'
    )
    reservations = relationship(
        'Reservation',
        secondary=diner_reservation_association,
        back_populates='diners'
    )

    def __repr__(self):
        return f'Diner {self.id}: {self.name}'


class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    dietary_restrictions = relationship(
        'DietaryRestriction', 
        secondary=restaurant_dietary_restriction_association, 
        back_populates='restaurants',
    )

    def __repr__(self):
        return f'Restaurant {self.id}: {self.name}'


class RestaurantTable(Base):
    __tablename__ = 'restaurant_tables'
    id = Column(Integer, primary_key=True)
    capacity = Column(Integer()) # In case we have 100
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    
    def __repr__(self):
        return f'RestaurantTable {self.id}: capacity: {self.capacity} with Restaurant {self.restaurant_id}'

class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey('restaurant_tables.id'), nullable=False)
    start_datetime = Column(DateTime())
    end_datetime = Column(DateTime())
    diners = relationship(
        'Diner', 
        secondary=diner_reservation_association, 
        back_populates='reservations'
    )
    def __repr__(self):
        return f'Reservation {self.id}: table: {self.table_id} from {self.start_datetime} to {self.end_datetime}'


class DietaryRestriction(Base):
    __tablename__ = 'dietary_restrictions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

    restaurants = relationship(
        'Restaurant',
        secondary=restaurant_dietary_restriction_association, 
        back_populates='dietary_restrictions'
    )

    diners = relationship(
        'Diner', 
        secondary=diner_dietary_restriction_association, 
        back_populates='dietary_restrictions'
    )

    def __repr__(self):
        return f'Dietary Restriction {self.id}: {self.name}'
