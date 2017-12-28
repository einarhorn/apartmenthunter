import unittest

from main.parsers.cpm_parser import CpmParser
from main.utils.database import create_database, connect_to_database, Apartment


class CpmParserTest(unittest.TestCase):
    def test_parse_single_page(self):
        url = 'http://cpm-apts.com/properties/1102-e-colorado-urbana-il/?tour=1'

        expected_page_dictionary = {
            'bathrooms': u'1.0-1.5',
            'description': u'Charming building located near the flourishing Philo Road Commercial District.\xa0Limited access building which includes washer/dryer, dishwasher, and balcony. Some units have Jacuzzi tub and lofted bedrooms.\nAsk about our $99.00 security deposit promotion!',
            'price': u'$580',
            'bedrooms': u'2 BR',
            'image_urls': [
                'http://cpm-apts.com/http://www.cpm-apts.com/wp-content/uploads/2016/02/1102-Colorado-1-of-7.jpg',
                'http://cpm-apts.com/http://www.cpm-apts.com/wp-content/uploads/2016/02/1102-Colorado-5-of-7.jpg',
                'http://cpm-apts.com/http://www.cpm-apts.com/wp-content/uploads/2016/02/1102-Colorado-6-of-7.jpg',
                'http://cpm-apts.com/http://www.cpm-apts.com/wp-content/uploads/2016/02/1102-Colorado-3-of-7.jpg',
                'http://cpm-apts.com/http://www.cpm-apts.com/wp-content/uploads/2016/02/1102-Colorado-4-of-7.jpg',
                'http://cpm-apts.com/http://www.cpm-apts.com/wp-content/uploads/2016/02/1102-Colorado-2-of-7.jpg'
            ],
            'floorplan_url': 0,
            'address': None,
            'name': u'1102 E. Colorado, Urbana IL',
            'url': 'http://cpm-apts.com/properties/1102-e-colorado-urbana-il/?tour=1',
            'leasing_period': '',
            'amenities': u'Balcony/Patio, Dishwasher, Washer/Dryer in Unit, '
        }

        cpm_parser = CpmParser()
        cpm_parser.parse_single_page(url)
        page_dictionary = cpm_parser.apartment_data[0]
        self.assertEquals(expected_page_dictionary, page_dictionary)

    def test_insertion_single_page(self):
        # Create database
        create_database('test_database.db')
        session = connect_to_database('test_database.db')

        # Create CPM instance
        url = 'http://cpm-apts.com/properties/1102-e-colorado-urbana-il/?tour=1'
        cpm_parser = CpmParser()
        cpm_parser.parse_single_page(url)
        cpm_parser.store_all_to_database(session)

        # Query database to check data was correctly inserted
        all_apartments = session.query(Apartment).all()
        self.assertEqual(url, all_apartments[0].url)
        self.assertEqual(u'2 BR', all_apartments[0].bedrooms)
        self.assertEqual(u'$580', all_apartments[0].price)

if __name__ == '__main__':
    unittest.main()