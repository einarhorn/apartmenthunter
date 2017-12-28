from unittest.case import TestCase
import unittest
from tests.parsers.cpm_parser_test import CpmParserTest
from tests.parsers.jsm_parser_test import JsmParserTest

runner = unittest.TextTestRunner()

result = runner.run(unittest.makeSuite(CpmParserTest))
result = runner.run(unittest.makeSuite(JsmParserTest))