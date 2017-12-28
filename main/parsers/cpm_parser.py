#coding: utf-8

import logging

from main.utils.database import Company, Image, Apartment, Amenity
from main.utils.core_utils import generate_soup


class CpmParser:
    """Handles the parsing of CPM website
    Parses CPM websites, and stores data to
    sqlite database
    """
    def __init__(self):
        """Initializer for CpmParser class
        Sets up relevant urls and data structures
        """

        self.base_url = 'http://cpm-apts.com/'
        self.base_url_apartments = self.base_url + "apartment/"
        self.start_url = self.base_url_apartments
        self.apartment_urls = []
        self.apartment_data = []

    def parse_all(self):
        """Single endpoint for automatically finding and
        parsing all CPM apartments. The parse results
        are stored in the self.apartment_data variable
        """

        # Generates a list of apartment urls
        self.parse_apartment_urls()

        # Parses each apartment url and stores it in apartment_data
        for apartment_url in self.apartment_urls:
            print("Parsing: ", apartment_url)
            self.parse_single_page(apartment_url)

    def parse_apartment_urls(self):
        """Finds the urls of all the apartments on the CPM website,
        and stores this in self.apartment_urls
        """

        # Generate soup for starting page
        soup = generate_soup(self.start_url)

        # Empties the urls list, in case it wasn't before
        self.apartment_urls = []

        # Get apartments in current page and store
        current_page_apartment_urls = self.list_get_apartment_urls(soup)
        self.apartment_urls = current_page_apartment_urls

    def list_get_apartment_urls(self, soup):
        """Gets a list of apartment urls shown in the current page

        Args:
            soup (BeautifulSoup): Soup instance of apartment list page

        Returns:
            list: List of urls of apartments in current page
        """

        # List of apartment urls extracted from page to return
        apartment_urls = []

        # Iterate over each apartment shown on current page
        list_container = soup.find(id='container')
        for divtag in list_container.find_all(class_='propertyItem'):

            # Find all links in this div tag
            anchor_tag = divtag.find('a', class_='card', href=True)

            # Extract the link from the anchor tag
            apartment_link = anchor_tag['href']

            # Extract the address here
            address_container = divtag.find(class_='cardAddress')
            address_container.br.replace_with(' ')
            address = address_container.text.strip()

            # Store the apartment link tuple
            apartment_urls.append((apartment_link, address))

        # Return list of apartments in current page
        return apartment_urls

    def parse_single_page(self, url_tuple):
        """Parses a single apartment page, given an apartment url

        Args:
            url_tuple (tuple): Url and address of page to parse
        """
        logging.info("Parsing %s", url_tuple)

        url = url_tuple[0]
        address = url_tuple[1]

        # Generate a soup instance for this url
        soup = generate_soup(url)

        # Each CPM apartment page, can consist of multiple apartments
        # This is because each apartment can have different leases with
        # different numbers of bedrooms and bathrooms
        for page in range(0, self.get_num_pages(soup)):

            # Dictionary to store the data in
            apartment_dict = {
                'url': url,
                'name': 0,
                'address': address,
                'bedrooms': 0,
                'bathrooms': 0,
                'price': 0,
                'leasing_period': '',
                'description': 0,
                'amenities': 0,
                'image_urls': 0,
                'floorplan_url': 0,
                'lat': 0,
                'lng': 0
            }

            # Parse the page for the relevant information
            self.get_apartment_name(soup, apartment_dict)
            self.get_apartment_stats(soup, apartment_dict, page)
            self.get_apartment_description(soup, apartment_dict)
            self.get_apartment_amenities(soup, apartment_dict)
            self.get_apartment_images(soup, apartment_dict)
            self.get_apartment_latlng(soup, apartment_dict)

            # Check if we failed to find any of the parameters and warn\
            skip=False
            for key, value in apartment_dict.iteritems():
                if value == 0:
                    logging.warn("Failed parsing %s", key)
                    if key == 'lat' or key == 'lng':
                        skip=True


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

        apartment_name_tag = soup.find(class_='pageTitle')
        title = apartment_name_tag.text.strip()
        apartment_dict['name'] = title

    def get_apartment_address(self, soup, apartment_dict):
        """Parse apartment page to find address
        NOTE: We don't actually parse the address at this step, this method
        is purely for consistency with other parsing classes. The address
        parse is done at the list extraction level, due to the fact that
        CPM doesn't provide address info at the apartment page level.

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """
        return

    def get_apartment_stats(self, soup, apartment_dict, page):
        """Parse apartment page to find apartment stats

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
            page (int): row of stats table to inspect for data
        """

        # Extract apartment stats table
        apartment_table = soup.find(id='room-type')
        table_rows = apartment_table.find('tbody').find_all('tr')

        # Get the appropriate row
        table_row = table_rows[page]

        # Extract data from the table columns
        table_cols = table_row.find_all('td')
        bedrooms = table_cols[0].text.strip()
        bathrooms = table_cols[1].text.strip()
        price = table_cols[3].text.strip()

        # Clean up bedroom, bathroom, and price to integers
        try:
            bedroom_int = int(bedrooms.split(' ')[0])
        except ValueError:
            bedroom_int = 1

        try:
            bathroom_int = int(float(bathrooms.split('-')[0]))
        except ValueError:
            # Bathroom is not an integer
            bathroom_int = 1

        try:
            price = price.replace(',', '')
            price_int = int(price[1:].split('-')[0])
        except:
            price_int = 0

        # Store data in dictionary
        apartment_dict['bedrooms'] = bedroom_int
        apartment_dict['bathrooms'] = bathroom_int
        apartment_dict['price'] = price_int


    def get_apartment_description(self, soup, apartment_dict):
        """Parse apartment page to find description

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """
        description_class = soup.find('div', id='building_desc')
        if not description_class:
            logging.warning("Failed to parse description")
            return
        else:
            apartment_dict['description'] = description_class.text.strip()

    def get_apartment_amenities(self, soup, apartment_dict):
        """Parse apartment page to find amenities

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """
        amenities_list_container = soup.find('div', id='amenities')
        amenities_list = []

        # Creates a comma seperated list of amenities
        for litag in amenities_list_container.find_all('li'):
            amenities_list.append(litag.text.strip())
        apartment_dict['amenities'] = amenities_list

    def get_apartment_images(self, soup, apartment_dict):
        """Parse apartment page to find images

        Args:
            soup (BeautifulSoup): soup instance of current page
            apartment_dict (dict): dictionary in which to store results
        """
        image_urls = []
        images_container = soup.find('div', id='carouselFull')

        # Iterate over image gallery, extracting image urls
        for anchor_tag in images_container.find_all('a', class_='galleryItem', href=True):
            image_urls.append(anchor_tag['href'])
        apartment_dict['image_urls'] = image_urls

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

    def get_num_pages(self, soup):
        """Gets the number of pages to generate for a given apartment
        (Each apartment page can contain multiple different numbers of bedrooms)

        Args:
            soup (BeautifulSoup): soup instance of current page

        Returns:
            number of pages as integer
        """
        apartment_table = soup.find(id='room-type')
        table_rows = apartment_table.find('tbody').find_all('tr')

        # Number of apartment pages corresponds to number of rows
        num_pages = len(table_rows)
        return num_pages



    def store_all_to_database(self, session):
        """Stores all apartment data to the given database

        Note:
            Expects the database to be devoid of any CPM objects

        Args:
            session (SQLAlchemy): SQLAlchemy database reference
        """

        description = 'Campus Property Management was founded in 1967 by Champaign resident and University of Illinois alumnus Erwin Goldfarb. Recognizing the need for expanded housing around the University, Erwin decided to start his own leasing company. Starting off with just one building, Erwin took pride in providing the best customer service to his tenants - even going so far as to lay carpet and painting apartments himself! Growing steadily through the years, the company built its first building from start to finish in 1983 and officially became Campus Property Management in 1988. Since those early years, CPM has grown to include 1,850 apartments which are home to 4,500 tenants each year! As our business continues to grow, we remain committed to our core values of integrity, commitment, innovation, opportunity and service. We are dedicated to providing comfortable and affordable housing with great customer service while continuing to be a proud part of the Illini community and giving back whenever we can!'

        # Insert a CPM company instance into the database
        current_company = Company(
            name='CPM',
            baseurl = 'http://www.cpm-apts.com/',
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

                # Connect floorplan to apartment
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
        # Write all the queries to database
        session.commit()