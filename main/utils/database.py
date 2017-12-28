import os
import logging
from sqlalchemy import Column, ForeignKey, Integer, String, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, joinedload, configure_mappers
from sqlalchemy import create_engine
from sqlalchemy_searchable import make_searchable
Base = declarative_base()

# Constants
database_filename = 'apartment_database.db'
entries_per_page = 18

# Make the database searchable
make_searchable()

class ApartmentRating(Base):
    """
    Rating object for apartments
    """
    __tablename__ = 'apartmentrating'
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)
    text = Column(String(1000), nullable=True)
    apartment_id = Column(Integer, ForeignKey('apartment.id'), nullable=False)

class AgencyRating(Base):
    """
    Rating object for leasing agencies
    """
    __tablename__ = 'agencyrating'
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)
    text = Column(String(1000), nullable=True)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)


class Company(Base):
    """
    Leasing company database schema
    """
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    ratings = relationship(AgencyRating)
    baseurl = Column(String(250), nullable=False)
    description = Column(String(2000), nullable=False)

class Image(Base):
    """
    Image database schema
    """
    __tablename__ = 'image'
    id = Column(Integer, primary_key=True)
    url = Column(String(250), nullable=False)
    apartment_id = Column(Integer, ForeignKey('apartment.id'), nullable=False)
    type = Column(Integer, nullable=False)
    image_index = Column(Integer, nullable=False)

class Amenity(Base):
    """
    Amenity databaes schema
    """
    __tablename__ = 'amenity'
    id = Column(Integer, primary_key=True)
    apartment_id = Column(Integer, ForeignKey('apartment.id'), nullable=False)
    amenity = Column(String(250), nullable=False)

class Apartment(Base):
    """
    Apartment database schema
    """
    __tablename__ = 'apartment'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'))
    company = relationship(Company)
    url = Column(String(250), nullable=False)
    name = Column(String(250), nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    address = Column(String(250), nullable=False)
    leasing_period = Column(String(250), nullable=False)
    description = Column(String(10000), nullable=False)
    amenities = relationship(Amenity)
    images = relationship(Image)
    lat = Column(String(250), nullable=False)
    lng = Column(String(250), nullable=False)
    ratings = relationship(ApartmentRating)


def create_database(filename=database_filename):
    """Handles the creation of apartment database
    Will delete any previous instance of the apartment database,
    if it exists
    """
    if os.path.isfile(filename):
        os.remove(filename)

    # Create an engine that stores data in the local directory's
    # sqlalchemy_example.db file.
    engine = create_engine('sqlite:///' + filename)
    configure_mappers()
    # Create all tables in the engine.
    Base.metadata.create_all(engine)

    logging.info("Created database")

def connect_to_database(filename=database_filename):
    """Handles the connection to a pre-existing apartment database

    Returns:
        SQLAlchemy session: Connection to database
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Setup database engine
    engine = create_engine('sqlite:///' + filename)
    configure_mappers()
    Base.metadata.bind = engine

    # Create a session instance, for sql query execution
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    logging.info("Successfully connected to database")

    # Return database session
    return session

def get_single_apartment(session, id):
    """Gets a single apartment database object with given id

    Args:
        id (int): id of apartment object

    Returns:
        sqlalchemy object (apartment entry)
    """
    apartment = session.query(Apartment).options(\
        joinedload(Apartment.images),\
        joinedload(Apartment.amenities),\
        joinedload(Apartment.company), \
        joinedload(Apartment.ratings) \
    ).filter(Apartment.id == id).first()
    return apartment

def get_all_apartments(
        session,
        current_page,
        filter,
        sortation=None,
        limit=entries_per_page,
    ):
    """Gets a list of apartment objects with a filter applied to it

    Args:
        session (sqlalchemy session instance): sqlalchemy connection to database
        current_page (int): current page of query to return
        filter (dictionary): filters to apply to query
        limit (int): number of entries to return

    Returns:
        list of sqlalchemy objects (apartment entries)
    """

    # Core query
    query = session.query(Apartment)\
        .join(Apartment.company)\
        .options( \
            joinedload(Apartment.images), \
            joinedload(Apartment.amenities), \
            joinedload(Apartment.company), \
            joinedload(Apartment.ratings) \
        )

    # Filter by keyword
    if filter['keywords'] is not None:
        print("Filtering on keyword", filter['keywords'])
        query = query.filter(Apartment.description.like('%' + filter['keywords'] + '%'))

    # Filter by agency
    if filter['agency'] is not None:
        print("Filtering on agency")
        query = query.filter(Company.name.like(filter['agency']))

    # Filter by min-price
    if filter['min_price'] is not None:
        print("Filtering on minprice")
        query = query.filter(Apartment.price >= filter['min_price'])

    # Filter by max-price
    if filter['max_price'] is not None:
        print("Filtering on maxprice")
        query = query.filter(Apartment.price <= filter['max_price'])

    # Filter by min-bedrooms
    if filter['min_bedrooms'] is not None:
        print("Filtering on minbedrooms")
        query = query.filter(Apartment.bedrooms >= filter['min_bedrooms'])

    # Filter by max-bedrooms
    if filter['max_bedrooms'] is not None:
        print("Filtering on maxbedrooms")
        query = query.filter(Apartment.bedrooms <= filter['max_bedrooms'])

    # Filter by min-bathrooms
    if filter['min_bathrooms'] is not None:
        print("Filtering on minbathrooms")
        query = query.filter(Apartment.bathrooms >= filter['min_bathrooms'])

    # Filter by max-bathrooms
    if filter['max_bathrooms'] is not None:
        print("Filtering on maxbathrooms")
        query = query.filter(Apartment.bathrooms <= filter['max_bathrooms'])

    # Order queries
    if sortation == 'price-inc':
        query = query.order_by(Apartment.price)
    if sortation == 'price-dec':
        query = query.order_by(desc(Apartment.price))
    if sortation == 'bedrooms-inc':
        query = query.order_by(Apartment.bedrooms)
    if sortation == 'bedrooms-dec':
        query = query.order_by(desc(Apartment.bedrooms))
    if sortation == 'bathrooms-inc':
        query = query.order_by(Apartment.bathrooms)
    if sortation == 'bathrooms-dec':
        query = query.order_by(desc(Apartment.bathrooms))
    if sortation == 'rating-inc':
        query = query.order_by(Apartment.ratings)
    if sortation == 'rating-dec':
        query = query.order_by(desc(Apartment.ratings))

    # Execute query
    num_entries = query.count()
    query = query.all()

    # Restrict results to current page
    if limit is not 0:
        # Calculate number of pages
        num_pages = num_entries / entries_per_page + 1

        start_entry = (current_page - 1) * entries_per_page
        end_entry = (current_page) * entries_per_page
        query = query[start_entry:end_entry]
    else:
        # In this case, we return all queries
        num_pages = 1

    # Return (filtered) query
    return query, num_pages

def save_review_to_database(session, id, rating, comment):
    # Create review object
    new_review = ApartmentRating(
        apartment_id=id,
        value=rating,
        text=comment
    )
    session.add(new_review)

    # Write all queries to the database
    session.commit()


def save_apartment_review_to_database(session, id, rating, comment):
    # Create review object
    new_review = AgencyRating(
        company_id=id,
        value=rating,
        text=comment
    )
    session.add(new_review)

    # Write all queries to the database
    session.commit()

def get_all_agencies(session):
    agencies = session.query(Company).options( \
        joinedload(Company.ratings)\
    )
    return agencies