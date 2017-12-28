import logging

from main.utils.database import Company, Image, Apartment, Amenity
from main.utils.core_utils import generate_soup


class JsmParser():
    """Handles the parsing of JSM website
    Parses JSM websites, and stores data to
    sqlite database
    """
    def __init__(self):
        """Initializer for JsmParser class
        Sets up relevant urls and data structures
        """

        self.base_url = 'https://apartments.jsmliving.com/'
        self.base_url_apartments = self.base_url + "apartments/"
        self.start_url = self.base_url_apartments + "?availability=37"
        self.apartment_urls = []
        self.apartment_data = []

    def parse_all(self):
        """Single endpoint for automatically finding and
        parsing all JSM apartments. The parse results
        are stored in the self.apartment_data variable
        """

        # Generates a list of apartment urls
        self.parse_apartment_urls()

        # Parses each apartment url and stores it in apartment_data
        for apartment_url in self.apartment_urls:
            self.parse_single_page(apartment_url)

    def parse_apartment_urls(self):
        """Finds the urls of all the apartments on the JSM website,
        and stores this in self.apartment_urls
        """

        # Generate soup for starting page
        soup = generate_soup(self.start_url)

        # Empties the urls list, in case it wasn't before
        self.apartment_urls = []

        # Get apartments in current page and store
        current_page_apartment_urls = self.list_get_apartment_urls(soup)
        self.apartment_urls = self.apartment_urls + current_page_apartment_urls

        # Check if there are more page to pull from
        while self.list_has_next_page(soup):
            soup = self.list_get_next_page(soup)

            # Get apartments in current page
            current_page_apartment_urls = self.list_get_apartment_urls(soup)
            self.apartment_urls = self.apartment_urls + current_page_apartment_urls

    def list_get_apartment_urls(self, soup):
        """Gets a list of apartment urls shown in the current page

        Args:
            soup (BeautifulSoup): Soup instance of apartment list page

        Returns:
            list: List of urls of apartments in current page
        """

        # List of apartment urls extracted from page
        apartment_urls = []

        # Each apartment entry exists as an 'li' tag in the 'ul' class 'units-grid'
        for ultag in soup.find_all('ul', {'class': 'units-grid'}):

            # Iterate over each apartment
            for litag in ultag.find_all('li'):

                # Find all links in this li tag
                all_anchors = litag.find_all('a', href=True)

                # Check that there were in fact anchor tags in the apartment 'li'
                if all_anchors and len(all_anchors) > 0:
                    # The link to the apartment is the first anchor element
                    apartment_anchor = all_anchors[0]

                    # Extract the apartment link from the anchor
                    apartment_link = apartment_anchor['href']

                    # Store the aparment link
                    apartment_urls.append(apartment_link)

        # Return list of apartments in current page
        return apartment_urls

    def list_has_next_page(self, soup):
        """Checks if the given list page has a "next" page

        Args:
            soup (BeautifulSoup): Soup instance of apartment list page

        Returns:
            True, if list has next page, false otherwise
        """

        # Check for the 'next page' element at the bottom of the page
        next_page_exists = soup.find('a', class_='pager pager-next')

        # If this element exists, there is a next page of apartments to parse
        if next_page_exists:
            return True
        else:
            return False

    def list_get_next_page(self, soup):
        """Gets the next list page url

        Args:
            soup (BeautifulSoup): Soup instance of apartment list page

        Returns:
            BeautifulSoup instance of next page, if it exists
        """
        # Get the 'next page' element at the bottom of the page
        next_page_tag = soup.find('a', class_='pager pager-next')

        # Extract the link from this element
        if next_page_tag:
            page_url = self.base_url_apartments + next_page_tag['href']
            return generate_soup(page_url)
        else:
            return None


    def parse_single_page(self, url):
        """Parses a single apartment page, given an apartment url

        Args:
            url (string): Url of page to parse
        """

        logging.info("Parsing %s", url)

        # Generate a soup instance for this url
        soup = generate_soup(self.base_url_apartments + url)

        # Dictionary to store data in
        apartment_dict = {
            'url': url,
            'name': 0,
            'address': 0,
            'bedrooms': 0,
            'bathrooms': 0,
            'price': 0,
            'leasing_period': 0,
            'description': 0,
            'amenities': 0,
            'image_urls': 0,
            'floorplan_url': 0,
            'lat': 0,
            'lng': 0
        }

        # Parse the page for the relevant information
        self.get_apartment_name(soup, apartment_dict)
        self.get_apartment_address(soup, apartment_dict)
        self.get_apartment_stats(soup, apartment_dict)
        self.get_apartment_description(soup, apartment_dict)
        self.get_apartment_amenities(soup, apartment_dict)
        self.get_apartment_images(soup, apartment_dict)
        self.get_apartment_floorplan(soup, apartment_dict)
        self.get_apartment_latlng(soup, apartment_dict)

        # Check if we failed to find any of the parameters
        skip=False
        for key, value in apartment_dict.iteritems():
            if value == 0:
                logging.warn("Failed parsing %s", key)
                if key == 'lat' or key == 'lng':
                    skip = True

        print(apartment_dict)
        # Store apartment data in list
        if skip is False:
            self.apartment_data.append(apartment_dict)

    def get_apartment_name(self, soup, apartment_dict):
        """Parse apartment page to find name

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """

        info_class = soup.find_all('div', {'class': 'info'})
        if info_class and len(info_class) > 0:
            info_class = info_class[0]
        else:
            logging.warning("Failed to parse apartment name")
            return None

        title = info_class.find('h1').text.strip()
        apartment_dict['name'] = title

    def get_apartment_address(self, soup, apartment_dict):
        """Parse apartment page to find address

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """

        info_class = soup.find_all('div', {'class': 'info'})
        if info_class and len(info_class) > 0:
            info_class = info_class[0]
            address = info_class.find('h2').text.strip()

            from parse import parse
            address = parse("Location: {}", address)[0]
            apartment_dict['address'] = address
        else:
            logging.warning("Failed to parse apartment address")
            return



    def get_apartment_stats(self, soup, apartment_dict):
        """Parse apartment page to find apartment stats

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
            page (int): row of stats table to inspect for data
        """

        # Get the stats element
        info_class = soup.find('div', {'class': 'info'})
        stats_class = info_class.find('div', class_='stats')
        stats_elements = stats_class.find_all('div', {'class': 'stat'})
        size = stats_elements[0].text.strip()

        # Parse size string
        # This is a string in the format: "Size: 1 BR/ 2 Baths"
        from parse import parse
        parsed_size = parse("Size: {}/{}", size)

        # Check if parse was successful
        if parsed_size:
            if parsed_size[0] == 'Efficiency':
                apartment_dict['bedrooms'] = 1
            else:
                bedrooms = parse("{} Bedrooms", parsed_size[0])
                try:
                    apartment_dict['bedrooms'] = int(bedrooms)
                except:
                    apartment_dict['bedrooms'] = 1

            bathrooms = parse("{} Baths", parsed_size[1])
            bathrooms_int = int(bathrooms[0])
            apartment_dict['bathrooms'] = bathrooms_int

        # Parse manually if not successful
        else:
            if size == 'Size: Efficiency':
                apartment_dict['bedrooms'] = 1
                apartment_dict['bathrooms'] = 1
            else:
                apartment_dict['bedrooms'] = 1
                apartment_dict['bathrooms'] = 1
                logging.warning("Failed to parse bedrooms/bathrooms")

        # Store the rest of the stats
        price = stats_elements[1].text.strip()
        try:
            price = price.replace(',', '')
            price_int = int(price[1:].split('-')[0])
        except:
            price_int = 0
        apartment_dict['price'] = price_int
        leasing_period = stats_elements[2].text.strip()
        apartment_dict['leasing_period'] = leasing_period

    def get_apartment_description(self, soup, apartment_dict):
        """Parse apartment page to find description

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """

        # Check for apartment description
        description_class = soup.find('div', class_='description')
        if not description_class:
            logging.warning("Failed to parse description")
            return

        # Store apartment description
        description_text = ''
        for ptag in description_class.find_all('p'):
            description_text += ptag.text.strip() + ' '
        apartment_dict['description'] = description_text

    def get_apartment_utilties(self, soup, apartment_dict):
        """Parse apartment page to find utilities

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """

        utility_fee_amount = soup.find('div', class_='utilityFeeAmount').text.strip()
        apartment_dict['utilities'] = utility_fee_amount

    def get_apartment_amenities(self, soup, apartment_dict):
        """Parse apartment page to find amenities

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """

        amenities_list_container = soup.find('div', class_='amenities')
        amenities_list = []
        for spantag in amenities_list_container.find_all('span', class_='amenity'):
            amenities_list.append(spantag.text.strip())
        apartment_dict['amenities'] = amenities_list

    def get_apartment_images(self, soup, apartment_dict):
        """Parse apartment page to find images

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """

        image_urls = []
        images_container = soup.find('div', class_='photos')
        images_container = images_container.find('div')

        # Iterate over images in gallery
        for image_container in images_container.find_all('div'):
            anchor_tag = image_container.find('a')
            if anchor_tag:
                image_urls.append(self.base_url + anchor_tag['href'])
        apartment_dict['image_urls'] = image_urls

    def get_apartment_floorplan(self, soup, apartment_dict):
        """Parse apartment page to find images

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """

        floor_plan_container = soup.find('div', class_='fl mb mr')
        if floor_plan_container:
            floor_plan_anchor = floor_plan_container.find('a')
            floor_plan_url = ''
            if floor_plan_anchor:
                floor_plan_url = self.base_url + floor_plan_anchor['href']
                apartment_dict['floorplan_url'] = floor_plan_url
                return

        logging.warning("Failed to parse floorplan")
        apartment_dict['floorplan_url'] = 0

    def get_apartment_latlng(self, soup, apartment_dict):
        """Query Google maps to access latlng

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """
        import googlemaps
        from datetime import datetime

        gmaps = googlemaps.Client(key='AIzaSyBxV4EAXU1aMLGU9bnokygGL92c2BxDzCE')

        # Geocoding an address
        geocode_result = gmaps.geocode(apartment_dict['address'])

        if len(geocode_result) > 0:
            # Store lat and lng
            apartment_dict['lat'] = geocode_result[0]['geometry']['location']['lat']
            apartment_dict['lng'] = geocode_result[0]['geometry']['location']['lng']
        else:
            print("Failed to find lat and lng values")


    def store_all_to_database(self, session):
        """Stores all apartment data to the given database

        Note:
            Expects the database to be devoid of any JSM objects

        Args:
            session (SQLAlchemy): SQLAlchemy database reference
        """

        description = 'Established in 1974, JSM is a family-owned provider of quality apartments. We offer a variety of units from studios to five bedrooms with every location benefitting from our award winning amenities, responsive 24 hour maintenance, and friendly property management staff. JSM Development began in Champaign, IL, and manages roughly 1,500 apartments and 450,000 sq/ft of commercial space. JSM has been a major contributor to the development of Campustown in Champaign and the East Campus area in Urbana at the University of Illinois. These popular locations are now home to major national retailers such as Urban Outfitters, Chipotle, Panera, Cold Stone Creamery, and Noodles & Co.'

        # Insert a JSM company instance into the database
        current_company = Company(
            name='JSM',
            baseurl='https://apartments.jsmliving.com/',
            description = description
        )
        session.add(current_company)

        # Iterate over the apartments, storing each in the database
        for apartment in self.apartment_data:
            logging.info("Inserting %s to database", apartment['name'])
            new_apartment = Apartment(
                company=current_company,
                url=apartment['url'],
                name=apartment['name'],
                bedrooms=apartment['bedrooms'],
                bathrooms=apartment['bathrooms'],
                price=apartment['price'],
                leasing_period=apartment['leasing_period'],
                description=apartment['description'],
                address=apartment['address'],
                lat=apartment['lat'],
                lng=apartment['lng']
            )
            session.add(new_apartment)

            # Insert images for the given apartment
            for index, image_url in enumerate(apartment['image_urls']):
                new_image = Image(
                    url=image_url,
                    apartment_id=new_apartment.id,
                    type=0,
                    image_index=index
                )
                session.add(new_image)

                # Connect images to apartment
                new_apartment.images.append(new_image)

            # Insert floorplan image, if it exists
            if apartment['floorplan_url'] != 0:
                new_floorplan_image = Image(
                    url=apartment['floorplan_url'],
                    apartment_id=new_apartment.id,
                    type=1,
                    image_index=len(apartment['image_urls'])
                )
                session.add(new_floorplan_image)

                # Connect images to apartment
                new_apartment.images.append(new_floorplan_image)

            # Insert amenities for the given apartment
            for amenity in apartment['amenities']:
                new_amenity = Amenity(
                    apartment_id=new_apartment.id,
                    amenity=amenity
                )
                session.add(new_amenity)

                # Connect amenity to apartment
                new_apartment.amenities.append(new_amenity)

        # Write all queries to the database
        session.commit()