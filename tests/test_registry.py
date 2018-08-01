
import unittest

from intermine.registry import *


class RegistryTest(unittest.TestCase):

    def test_getInfo(self):
        # function returns none is everything runs fine
        self.assertEqual(getInfo('mock'), None)
        # function returns a message if anything goes wrong,


    def test_getMines(self):
        # function returns none is everything runs fine
        self.assertEqual(getMines('mock'), None)
        # function returns a message if anything goes wrong,
    

if __name__ == '__main__':
    unittest.main()
