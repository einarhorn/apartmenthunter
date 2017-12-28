import unittest

from main.parsers.jsm_parser import JsmParser
from main.utils.database import create_database, connect_to_database, Apartment


class JsmParserTest(unittest.TestCase):
    def test_parse_single_page(self):
        url = 'https://apartments.jsmliving.com/apartments/?unit_type_id=658'

        expected_page_dictionary = {
            'bathrooms': u'1 Baths',
            'description': u'Beautifully renovated units include new modern kitchens, new appliances, renovated bathrooms, and new flooring. Incredible location 2 blocks from Armory and Ice Arena! Secure entry! Rent includes monthly pest control, trash removal, access to the JSM Fitness Center and the\xa0JSM VIP Program\xa0with over $200 in savings, and a prompt, courteous, efficient maintenance staff. Leased parking available ',
            'price': u'$585 - $615',
            'bedrooms': 1,
            'image_urls': [
                'https://apartments.jsmliving.com//uploads/application/images/1000/6w4a0v9p83zx4nilomxrzy5sxeo3lvpiicha5q8xgwz17u0e2e.jpg',
                'https://apartments.jsmliving.com//uploads/application/images/1000/qvgnma3hvj5neipki5euega2dmv4a2lztgwmixydu1svg5ot7w.jpg',
                'https://apartments.jsmliving.com//uploads/application/images/1000/2g7k2tsh4f9gl3p1uqfk2n9dgt0btf1k5yfqux84x8mnvqq09u.jpg',
                'https://apartments.jsmliving.com//uploads/application/images/1000/rer0dc3284aiclbieoxzj54y3tk70blk14oqk28i2wnn22nadm.jpg',
                'https://apartments.jsmliving.com//uploads/application/images/1000/7y4adjsdkfapg7codphrmelp8armibzta5bootol97povqoe2a.jpg',
                'https://apartments.jsmliving.com//uploads/application/images/1000/uqfumo3yi9ost7flq0w4ulhwiqif5g6qlyzw0bvmienshhtbyk.jpg'
            ],
            'floorplan_url': 'https://apartments.jsmliving.com//uploads/application/images/1000/shidbirmkmtycrm6qrc8g8v58yu4nb4n0o7ackbmiuqrovi3ww.jpg',
            'address': u'Location: 105 E Chalmers St, Champaign, IL, 61820, US',
            'name': u'Chalmers Manor - 105 E. Chalmers - Efficiency',
            'url': 'https://apartments.jsmliving.com/apartments/?unit_type_id=658',
            'leasing_period': u'Fall 2018/19',
            'amenities': u'Secure Building, On-Site Laundry Facilities, Leased Parking, JSM VIP Program Access, Great Location, Furnished, Building Security System, Air Conditioned, Access to JSM Fitness Center, '
        }


        jsm_parser = JsmParser()
        jsm_parser.parse_single_page(url)
        page_dictionary = jsm_parser.apartment_data[0]
        self.assertEquals(expected_page_dictionary, page_dictionary)

    def test_insertion_single_page(self):
        # Create database
        create_database('test_database.db')
        session = connect_to_database('test_database.db')

        # Create JSM instance
        url = 'https://apartments.jsmliving.com/apartments/?unit_type_id=658'
        jsm_parser = JsmParser()
        jsm_parser.parse_single_page(url)
        jsm_parser.store_all_to_database(session)

        # Query database to check data was correctly inserted
        all_apartments = session.query(Apartment).all()
        self.assertEqual(1, len(all_apartments))
        self.assertEqual('https://apartments.jsmliving.com/apartments/?unit_type_id=658', all_apartments[0].url)
        self.assertEqual(1, all_apartments[0].bedrooms)
        self.assertEqual(u'$585 - $615', all_apartments[0].price)

if __name__ == '__main__':
    unittest.main()