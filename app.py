from main.utils.database import get_all_apartments, connect_to_database, get_single_apartment, save_review_to_database, get_all_agencies, save_apartment_review_to_database
from flask import Flask, render_template, request, json
app = Flask(__name__)

@app.route('/')
def index():
    """Called when '/' is loaded, simply returns the home page html file

    Returns:
        rendered index.html file
    """
    return render_template(
        'index.html',
        title='Home'
    )

@app.route('/map')
def map():
    """Called when '/map' is loaded, returns the map page with apartment information

    Returns:
        rendered map.html file
    """

    # Pull filter information from Flask request object
    filter = extract_filter_object()

    # Get list of apartments for the map
    apartments = load_all_apartments_for_map(filter)

    # Render template with apartment list
    return render_template(
        'map.html',
        title='Housing Map',
        apartments=apartments,
        filter=filter
    )

def extract_filter_object():
    """Extracts the filter data from the Flask request object

    Returns:
        dictionary representation of filter requested by user
    """

    # Extract keywords
    keywords = request.args.get('search-keyword', default=None, type=str)
    if keywords == '':
        keywords = None

    # Extract agency
    agency = request.args.get('agency', default=None, type=str)
    if agency == 'any':
        agency = None

    # Extract all other integer type filters
    min_price = request.args.get('min-price', default=None, type=int)
    max_price = request.args.get('max-price', default=None, type=int)
    min_bedrooms = request.args.get('min-bedrooms', default=None, type=int)
    max_bedrooms = request.args.get('max-bedrooms', default=None, type=int)
    min_bathrooms = request.args.get('min-bathrooms', default=None, type=int)
    max_bathrooms = request.args.get('max-bathrooms', default=None, type=int)

    # Store in dictionary
    filter = {
        'keywords': keywords,
        'agency': agency,
        'min_price': min_price,
        'max_price': max_price,
        'min_bedrooms': min_bedrooms,
        'max_bedrooms': max_bedrooms,
        'min_bathrooms': min_bathrooms,
        'max_bathrooms': max_bathrooms,
    }

    # Return filter
    return filter


def load_all_apartments_for_map(filter):
    """Loads all apartments for map page

    Args:
        filter (dictionary): filter to apply to search results

    Returns:
        list of apartment dictionary objects
    """

    # Create database session and get apartment objects
    session = connect_to_database('main/apartment_database.db')
    current_page = 1
    apartment_objects, num_pages = get_all_apartments(
        session,
        current_page,
        filter,
        limit=0
    )

    # Convert database objects to list of dictionaries
    apartment_list = []
    for u in apartment_objects:
        apartment_dict = convert_database_apartment(u)
        apartment_list.append(apartment_dict)

    # Return list of dictionaries
    return apartment_list

def convert_database_apartment(database_object):
    """Given a database apartment object, converts it to a dictionary

    Args:
        database_object (sqlalchemy apartment object): apartment object from database

    Returns:
        dictionary representation of apartment object
    """

    # Generate apartment dictionary
    apartment_dict = {
        'bathrooms': database_object.__dict__['bathrooms'],
        'description': database_object.__dict__['description'],
        'url': database_object.__dict__['url'],
        'price': database_object.__dict__['price'],
        'bedrooms': database_object.__dict__['bedrooms'],
        'leasing_period': database_object.__dict__['leasing_period'],
        'address': database_object.__dict__['address'],
        'id': database_object.__dict__['id'],
        'name': database_object.__dict__['name'],
        'lat': database_object.__dict__['lat'],
        'lng': database_object.__dict__['lng']
    }

    # Extract images (from separate table)
    image_list = []
    for image_object in database_object.__dict__['images']:
        image_entry = {
            'image_index': image_object.__dict__['image_index'],
            'url': image_object.__dict__['url'],
            'type': image_object.__dict__['type']
        }
        image_list.append(image_entry)

    # Sort the images according to the image_index
    from operator import itemgetter
    sorted_images = sorted(image_list, key=itemgetter('image_index'))
    apartment_dict['images'] = sorted_images

    # Load leasing agency (from separate table)
    agency_dict = database_object.__dict__['company'].__dict__
    apartment_dict['company'] = agency_dict['name']

    # Load amenities (from separate table)
    amenities_list = []
    for amenity in database_object.__dict__['amenities']:
        amenity_entry = {
            'amenity': amenity.__dict__['amenity']
        }
        amenities_list.append(amenity_entry)
    apartment_dict['amenities'] = amenities_list

    # Load reviews (from separate table)
    reviews_list = []
    for review in database_object.__dict__['ratings']:
        rating_entry = {
            'id': review.__dict__['id'],
            'value': review.__dict__['value'],
            'text': review.__dict__['text']
        }
        print(rating_entry)
        reviews_list.append(rating_entry)
    apartment_dict['ratings'] = reviews_list

    # Return dictionary
    return apartment_dict

@app.route('/apartments')
def apartments():
    """Called when '/apartments' page is queried

    Returns:
        rendered apartments.html file
    """

    # Extract current page from url
    current_page = request.args.get('page', default=1, type=int)

    # Generate filter dictionary from Flask request object
    filter = extract_filter_object()

    # Find which item to sort on
    sortation = request.args.get('sort', default=None, type=str)
    print("Sort: ", sortation)
    if sortation is None:
        sortation = "price-inc"

    # Load apartment data from database
    apartment_data, num_pages = load_apartments(
        filter,
        current_page,
        sortation
    )

    # Return rendered template
    return render_template(
        'apartments.html',
        apartments=apartment_data,
        current_page=current_page,
        num_pages=num_pages,
        filter=filter,
        has_previous_page=has_previous_page(current_page),
        has_next_page=has_next_page(current_page, num_pages),
        active_index=calculate_active_index(current_page, num_pages),
        show_paging_index=calculate_paging_index(num_pages),
        page_url=generate_page_url(filter),
        page_numbers=generate_paging_numbers(current_page, num_pages),
        sortation=sortation
    )

def calculate_active_index(current_page, num_pages):
    """Calculates the paging index (1-5) to hightlight
    (There are 5 buttons on the paging view, the paging index is the one that is highlighted)

    Args:
        current_page (int): current page user is one
        num_pages (int): number of pages in query

    Returns:
        integer index (1-5) to highlight
    """

    # Calculate active_index
    if current_page == 1:
        active_index = 1
    elif current_page == 2:
        active_index = 2
    elif current_page == 3:
        active_index = 3
    elif current_page == num_pages - 1:
        active_index = 4
    elif current_page == 4 and current_page == num_pages:
        active_index = 4
    elif current_page == num_pages:
        active_index = 5
    else:
        active_index = 3

    # Return active index
    return active_index

def calculate_paging_index(num_pages):
    """Calculate which of the five pagination links to show
    e.g. if there are three pages of results, only show the first three links (Page 1, Page 2, Page 3)
    e.g. if there are 10 pages of results, only show the first five links

    Args:
        num_pages (int): number of pages in query

    Returns:
        list of five booleans
    """

    show_paging_index = []
    for i in range(1, 6):
        if num_pages >= i:
            show_paging_index.append(True)
        else:
            show_paging_index.append(False)
    return show_paging_index

def generate_page_url(filter):
    """Generate a url with the current query filled in
    Filter url takes the form:
    "?search-keyword={}&agency={}&min-price={}&max-price={}&min-bedrooms={}&max-bedrooms={}&min-bathrooms={}&max-bathrooms={}"

    This function simply takes the current filter, and fills in the blanks

    Args:
        filter (dictionary): current filter

    Returns:
        url with filters included in it
    """

    # Create a modified filter dictionary, with minor changes to fit it for a url
    filter_for_url = {}
    for key, value in filter.iteritems():
        if key == 'keywords' and value is None:
            filter_for_url[key] = ''
        elif value is None:
            filter_for_url[key] = 'any'
        else:
            filter_for_url[key] = value

    # Format the page_url string with values from the filter
    page_url = "?search-keyword={}&agency={}&min-price={}&max-price={}&min-bedrooms={}&max-bedrooms={}&min-bathrooms={}&max-bathrooms={}"
    page_url = page_url.format(
        filter_for_url['keywords'],
        filter_for_url['agency'],
        filter_for_url['min_price'],
        filter_for_url['max_price'],
        filter_for_url['min_bedrooms'],
        filter_for_url['max_bedrooms'],
        filter_for_url['min_bathrooms'],
        filter_for_url['max_bathrooms']
    )

    # Return the page_url
    return page_url

def generate_paging_numbers(current_page, num_pages):
    """Generate list of 5 numbers to display for paging cheme

    Args:
        current_page (int): current selected page
        num_pages (int): number of pages in query

    Returns:
       list of paging numbers
    """

    # Generate paging numbers
    if num_pages <= 5 or current_page <= 3:
        page_numbers = [1,2,3,4,5]
    else:
        if current_page == num_pages or current_page == num_pages - 1:
            page_numbers = [num_pages-4,num_pages-3,num_pages-2,num_pages-1,num_pages]
        else:
            page_numbers = [current_page-2, current_page-1, current_page, current_page+1, current_page+2]
    return page_numbers

def has_next_page(current_page, num_pages):
    """Checks whether there is a next page in the query

    Args:
        current_page (int): current selected page
        num_pages (int): number of pages in query

    Returns:
       True, if there is a next page in the query
    """
    if current_page < num_pages:
        return True
    else:
        return False

def has_previous_page(current_page):
    """Checks whether there is a previous page in the query

    Args:
        current_page (int): current selected page
        num_pages (int): number of pages in query

    Returns:
       True, if there is a previous page in the query
    """
    if current_page > 1:
        return True
    else:
        return False


def load_apartments(
        filter,
        current_page,
        sortation
    ):
    """Loads list of apartments from database, with filter applied to it

    Args:
        filter (dictionary): filter used by user
        current_page (int): current selected page,
        sortation (str): column to sort by

    Returns:
       List of dictionary representation of apartments
    """

    # Connect to database and query for apartments
    session = connect_to_database('main/apartment_database.db')
    apartment_objects, num_pages = get_all_apartments(
        session,
        current_page,
        filter,
        sortation
    )

    # Convert database objects to dictionaries
    apartment_list = []
    for u in apartment_objects:
        apartment_dict = convert_database_apartment(u)
        apartment_list.append(apartment_dict)

    # Return list of dictionaries
    return apartment_list, num_pages

@app.route('/apartments/detail')
def apartment():
    """Called when '/apartments/detail' page is loaded
    Note: Expects an id value to be passed along in the url

    Returns:
       Rendered apartment.html page
    """

    # Extract id from url
    id = request.args.get('id', default=0, type=int)

    # Flag to represent whether apartment id is valid
    invalid_id = False

    # Retrieve apartment dictionary
    apartment = load_apartment(id)
    if apartment is None:
        invalid_id = True

    # Render apartment page
    return render_template(
        'apartment.html',
        id=id,
        apartment=load_apartment(id),
        invalid_id = invalid_id
    )

def load_apartment(id):
    """Loads single apartment from database, for given id

    Args:
        id (int): apartment id to load

    Returns:
        apartment as dictionary
    """

    # Connect to database and get apartment object
    session = connect_to_database('main/apartment_database.db')
    apartment_object = get_single_apartment(session, id)

    # Converts database object to dictionary
    if apartment_object:
        apartment_dict = convert_database_apartment(apartment_object)
        return apartment_dict
    else:
        return None

@app.route('/saveReview', methods=['POST'])
def save_review():
    apartment_id = request.form['id']
    rating =  request.form['rating']
    comment = request.form['comment']

    # Insert to database
    session = connect_to_database('main/apartment_database.db')
    save_review_to_database(session, apartment_id, rating, comment)

    # Return success status
    return json.dumps({'status':'OK'})

@app.route('/saveAgencyReview', methods=['POST'])
def save_agency_review():
    agency_id = request.form['id']
    rating =  request.form['rating']
    comment = request.form['comment']
    print("Received: ", rating, comment, agency_id)

    # Insert to database
    session = connect_to_database('main/apartment_database.db')
    save_apartment_review_to_database(session, agency_id, rating, comment)

    # Return success status
    return json.dumps({'status':'OK'})

@app.route('/agencies')
def agencies():
    agencies = get_agencies()

    return render_template(
        'agencies.html',
        agencies=agencies
    )

def get_agencies():
    session = connect_to_database('main/apartment_database.db')
    agencies_object = get_all_agencies(session)

    agencies_list = []
    for agency in agencies_object:
        agency_dict = {
            'id': agency.__dict__['id'],
            'name': agency.__dict__['name'],
            'baseurl': agency.__dict__['baseurl'],
            'description': agency.__dict__['description']
        }

        rating_list = []
        for rating in agency.__dict__['ratings']:
            rating_dict = {
                'text': rating.__dict__['text'],
                'value': rating.__dict__['value']
            }
            rating_list.append(rating_dict)

        agency_dict['ratings'] = rating_list

        agencies_list.append(agency_dict)

    return agencies_list



if __name__ == '__main__':
    app.run()