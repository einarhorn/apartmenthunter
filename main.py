from main.parsers.cpm_parser import CpmParser
from main.parsers.jsm_parser import JsmParser
from main.utils.database import create_database, connect_to_database
from main.utils.core_utils import setup_logger



def main():
    """Handles the parsing and creation of apartment database
    Parses JSM and CPM websites, and stores data to
    sqlite database
    """

    # Setup logger
    setup_logger()

    # Setup the database
    create_database()
    session = connect_to_database()

    # Parse CPM Apartments
    cpm_parser = CpmParser()
    cpm_parser.parse_all()
    cpm_parser.store_all_to_database(session)

    # Parse JSM Apartments
    jsm_parser = JsmParser()
    jsm_parser.parse_all()
    jsm_parser.store_all_to_database(session)


if __name__ == "__main__":
    main()