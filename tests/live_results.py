import sys
import os
sys.path.insert(0, os.getcwd())

import unittest
from intermine.webservice import Service
from intermine.errors import WebserviceError

class LiveResultsTest(unittest.TestCase):

    TEST_ROOT = os.getenv("TESTMODEL_URL", "http://localhost/intermine-test/service")

    SERVICE = Service(TEST_ROOT)

    def testLazyReferenceFetching(self):
        results = self.SERVICE.select("Department.*").results()
        managers = map(lambda x: x.manager.name, results)
        expected = [
            'EmployeeA1',
            'EmployeeB1',
            'EmployeeB3',
            'Jennifer Taylor-Clarke',
            'David Brent',
            'Keith Bishop',
            'Glynn Williams',
            'Neil Godwin',
            'Tatjana Berkel',
            u'Sinan Tur\xe7ulu',
            'Bernd Stromberg',
            'Timo Becker',
            'Dr. Stefan Heinemann',
            'Burkhardt Wutke',
            u'Frank M\xf6llers',
            'Charles Miner',
            'Michael Scott',
            'Angela',
            'Lonnis Collins',
            'Meredith Palmer',
            'Juliette Lebrac',
            'Gilles Triquet',
            'Jacques Plagnol Jacques',
            u'Didier Legu\xe9lec',
            'Joel Liotard',
            "Bwa'h Ha Ha",
            'Quote Leader',
            'Separator Leader',
            'Slash Leader',
            'XML Leader']

        self.assertEqual(expected, managers)

    def testLazyReferenceFetching(self):
        dave = self.SERVICE.select("Employee.*").where(name = "David Brent").one()
        self.assertEqual("Sales", dave.department.name)
        self.assertIsNotNone(dave.address)

        # Can handle null references.
        b1 = self.SERVICE.select("Employee.*").where(name = "EmployeeB1").one();
        self.assertIsNone(b1.address)

    def testLazyCollectionFetching(self):
        results = self.SERVICE.select("Department.*").results()
        age_sum = reduce(lambda x, y: x + reduce(lambda a, b: a + b.age, y.employees, 0), results, 0)
        self.assertEqual(5924, age_sum)

        # Can handle empty collections as well as populated ones.
        banks = self.SERVICE.select("Bank.*").results()
        self.assertEqual([1, 0, 0, 2, 2], [len(bank.corporateCustomers) for bank in banks])

    def testAllFormats(self):
        q = self.SERVICE.select("Manager.age")

        expected_sum = 1383

        self.assertEqual(expected_sum, sum(map(lambda x: x.age, q.results(row="object"))))
        self.assertEqual(expected_sum, sum(map(lambda x: x.age, q.results(row="objects"))))
        self.assertEqual(expected_sum, sum(map(lambda x: x.age, q.results(row="jsonobjects"))))

        self.assertEqual(expected_sum, sum(map(lambda x: x["age"], q.results(row="rr"))))
        self.assertEqual(expected_sum, sum(map(lambda x: x[0], q.results(row="rr"))))
        self.assertEqual(expected_sum, sum(map(lambda x: x("age"), q.results(row="rr"))))
        self.assertEqual(expected_sum, sum(map(lambda x: x(0), q.results(row="rr"))))

        self.assertEqual(expected_sum, sum(map(lambda x: x["Manager.age"], q.results(row="dict"))))
        self.assertEqual(expected_sum, sum(map(lambda x: x[0], q.results(row="list"))))

        self.assertEqual(expected_sum, sum(map(lambda x: x[0]["value"], q.results(row="jsonrows"))))

        import csv
        csvReader = csv.reader(q.results(row="csv"), delimiter=",", quotechar='"')
        self.assertEqual(expected_sum, sum(map(lambda x: int(x[0]), csvReader)))
        tsvReader = csv.reader(q.results(row="tsv"), delimiter="\t")
        self.assertEqual(expected_sum, sum(map(lambda x: int(x[0]), tsvReader)))

    def testModelClassAutoloading(self):
        q = self.SERVICE.model.Manager.select("name", "age")
        expected_sum = 1383

        self.assertEqual(expected_sum, sum(map(lambda x: x.age, q.results(row="object"))))

    def testSearch(self):
        res, facs = self.SERVICE.search('david')
        self.assertEqual(2, len(res))
        self.assertEqual(1, facs['Category']['Manager'])

        res, facs = self.SERVICE.search('david', Category = 'Department')
        self.assertEqual(1, len(res))
        self.assertEqual('Sales', res[0]['fields']['name'])

    def test_user_registration(self):
        username = 'mayfly@noreply.intermine.org'
        password = 'yolo'
        try:
            s = Service(self.SERVICE.root, username, password)
            s.deregister(s.get_deregistration_token())
        except:
            pass

        s = self.SERVICE.register(username, password)

        self.assertEqual(s.root, self.SERVICE.root)
        self.assertEqual([], s.get_all_lists())

        drt = s.get_deregistration_token()
        s.deregister(drt)

        with self.assertRaises(WebserviceError):
            s.get_all_lists()

if __name__ == '__main__':
    unittest.main()

