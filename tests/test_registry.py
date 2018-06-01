
import unittest

from ..intermine import registry


class RegistryTest(unittest.TestCase):

    def test_getInfo(self):
        # function returns none is everything runs fine
        self.assertEqual(registry.getInfo('flymine'), None)
        # function returns a message if anything goes wrong,
        # example: mine is not correct
        self.assertEqual(registry.getData('flymin'), "No such mine available")

    def test_getData(self):
        # function returns none is everything runs fine
        self.assertEqual(registry.getData('flymine'), None)
        # function returns a message if anything goes wrong,
        # example: mine is not correct
        self.assertEqual(registry.getData('flymin'), "No such mine available")

    def test_getMines(self):
        # function returns none is everything runs fine
        self.assertEqual(registry.getMines('D. melanogaster'), None)
        # function returns a message if anything goes wrong,
        # example: organism name is not correct
        self.assertEqual(registry.getMines('D. \
            melanogaste'), "No such mine available")


if __name__ == '__main__':
    unittest.main()
