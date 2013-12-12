import sys
import os
sys.path.insert(0, os.getcwd())

import unittest
from intermine.webservice import Service

class LiveResultsTest(unittest.TestCase):

    TEST_ROOT = os.getenv("TESTMODEL_URL", "http://localhost/intermine-test/service")

    SERVICE = Service(TEST_ROOT)

    def testGetWidgets(self):

        widgets = self.SERVICE.widgets
        self.assertTrue(len(widgets) > 0, msg = "No widgets were found")
        self.assertTrue('age_groups' in widgets, msg = "Could not find age_groups")

