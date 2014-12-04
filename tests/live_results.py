from __future__ import unicode_literals

import sys
import os
import uuid
import csv
sys.path.insert(0, os.getcwd())

import unittest
from intermine.webservice import Service
from intermine.errors import WebserviceError

try:
    from functools import reduce
except ImportError:
    pass # py3k import.

PY3K = sys.version_info >= (3,0)

def unicode_csv_reader(data, **kwargs):
    """Only needed in py2.x"""
    reader = csv.reader(utf_8_encoder(data), **kwargs)
    for row in reader:
        # Decode back.
        yield [cell.decode('utf-8') for cell in row]

def utf_8_encoder(unicode_data):
    for line in unicode_data:
        yield line.encode('utf-8')

class LiveResultsTest(unittest.TestCase):

    TEST_ROOT = os.getenv("TESTMODEL_URL", "http://localhost/intermine-test/service")

    SERVICE = Service(TEST_ROOT)

    def setUp(self):
        self.manager_q = self.SERVICE.select('Manager.age', 'Manager.name')
        self.manager_age_sum = 1383

    def testLazyReferenceFetching(self):
        departments = self.SERVICE.select("Department.*").results()
        managers = [d.manager.name for d in departments]
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
            'Sinan Tur\xe7ulu',
            'Bernd Stromberg',
            'Timo Becker',
            'Dr. Stefan Heinemann',
            'Burkhardt Wutke',
            'Frank M\xf6llers',
            'Charles Miner',
            'Michael Scott',
            'Angela',
            'Lonnis Collins',
            'Meredith Palmer',
            'Juliette Lebrac',
            'Gilles Triquet',
            'Jacques Plagnol Jacques',
            'Didier Legu\xe9lec',
            'Joel Liotard',
            "Bwa'h Ha Ha",
            'Quote Leader',
            'Separator Leader',
            'Slash Leader',
            'XML Leader']

        self.assertEqual(expected, managers)

    def assertIsNotNone(self, *args, **kwargs):
        if hasattr(unittest.TestCase, 'assertIsNotNone'): # py2.6 workaround
            return unittest.TestCase.assertIsNotNone(self, *args, **kwargs)
        thing = args[0]
        if thing is None:
            raise Exception("It is None")

    def assertIsNone(self, *args, **kwargs):
        if hasattr(unittest.TestCase, 'assertIsNone'): # py2.6 workaround
            return unittest.TestCase.assertIsNone(self, *args, **kwargs)
        thing = args[0]
        if thing is not None:
            raise Exception("{0} is not None".format(thing))

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

    def assertManagerAgeIsSum(self, fmt, accessor):
        total = sum(accessor(x) for x in self.manager_q.results(row = fmt))
        self.assertEqual(self.manager_age_sum, total)

    def test_attr_access(self):
        for synonym in ['object', 'objects', 'jsonobjects']:
            self.assertManagerAgeIsSum(synonym, lambda row: row.age)

    def test_rr_indexed_access(self):
        self.assertManagerAgeIsSum('rr', lambda row: row['age'])
        self.assertManagerAgeIsSum('rr', lambda row: row[0])

    def test_row_as_function(self):
        self.assertManagerAgeIsSum('rr', lambda row: row('age'))
        self.assertManagerAgeIsSum('rr', lambda row: row(0))

    def test_dict_row(self):
        self.assertManagerAgeIsSum('dict', lambda row: row['Manager.age'])

    def test_list_row(self):
        self.assertManagerAgeIsSum('list', lambda row: row[0])

    def test_json_rows(self):
        self.assertManagerAgeIsSum('jsonrows', lambda row: row[0]['value'])

    def test_csv(self):
        if PY3K: # string handling differences
            parse = lambda data: csv.reader(data, delimiter = ',', quotechar = '"')
        else:
            parse = lambda data: unicode_csv_reader(data, delimiter = b',', quotechar = b'"')

        results = self.manager_q.results(row = 'csv')
        reader = parse(results)
        self.assertEqual(self.manager_age_sum, sum(int(row[0]) for row in reader))

    def test_tsv(self):
        if PY3K: # string handling differences
            parse = lambda data: csv.reader(data, delimiter = '\t')
        else:
            parse = lambda data: unicode_csv_reader(data, delimiter = b'\t')

        results = self.manager_q.results(row = 'tsv')
        reader = parse(results)
        self.assertEqual(self.manager_age_sum, sum(int(row[0]) for row in reader))

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
        username = 'mayfly-{0}@noreply.intermine.org'.format(uuid.uuid4())
        password = 'yolo'
        try:
            s = Service(self.SERVICE.root, username, password)
            s.deregister(s.get_deregistration_token())
        except:
            pass

        s = self.SERVICE.register(username, password)

        self.assertEqual(s.root, self.SERVICE.root)
        self.assertEqual(2, len(s.get_all_lists()))

        drt = s.get_deregistration_token()
        s.deregister(drt)

        self.assertRaises(WebserviceError, s.get_all_lists)

    def test_templates(self):
        names = self.SERVICE.templates.keys()
        self.assertTrue(len(names))

        t0 = self.SERVICE.get_template('CEO_Rivals')
        c = t0.count()
        self.assertTrue(c, msg = "{0.name} should return some results".format(t0))

if __name__ == '__main__':
    unittest.main()

