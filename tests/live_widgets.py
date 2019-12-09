from intermine.webservice import Service
import unittest
import sys
import os
sys.path.insert(0, os.getcwd())


class LiveResultsTest(unittest.TestCase):

    TEST_ROOT = os.getenv(
        "TESTMODEL_URL", "http://localhost:8080/intermine-demo/service")

    SERVICE = Service(TEST_ROOT)

    def testGetWidgets(self):

        widgets = self.SERVICE.widgets
        self.assertTrue(len(widgets) > 0, msg="No widgets were found")
        self.assertTrue('age_groups' in widgets,
                        msg="Could not find age_groups")
