from bs4 import BeautifulSoup
import logging

def generate_soup(url, use_http=True):
    """Generates a BeautifulSoup instance for a given url

    Args:
        url (string): url to create soup instance for

    Returns:
        soup instance for given url
    """
    import urllib2
    opener = urllib2.build_opener()
    if use_http:
        opener.add_handler(urllib2.HTTPHandler())
    else:
        opener.add_handler(urllib2.HTTPSHandler())
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0')]
    # r = opener.open(url).read()

    try:
        r = opener.open(url).read()
    except urllib2.HTTPError, e:
        print e.code
        print e.msg
        print e.headers
        print e.fp.read()

    soup = BeautifulSoup(r, "lxml")
    return soup

def setup_logger():
    """
    Sets up the logger to write to a file and the console
    """
    logging.basicConfig(filename='parse_log.log', level=logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("Logger successfully setup")