from __future__ import unicode_literals

from intermine.webservice import Service
import os
import sys
import logging
import unittest
import codecs
from contextlib import closing

sys.path.insert(0, os.getcwd())

logging.basicConfig()


def emp_rows_without_ids(bag):
    return [row[:3] + row[4:] for row in bag.to_query().rows()]


with closing(codecs.open('tests/data/unicode-names.txt', 'r', 'UTF-8')) as f:
    UNICODE_NAMES = [line.strip() for line in f]

# This is coded all as one enormous test so that we can do
# a universal clean-up at the end.


class LiveListTest(unittest.TestCase):

    LOG = logging.getLogger('live-list-test')
    TEST_ROOT = os.getenv("TESTMODEL_URL",
                          "http://localhost:8080/intermine-demo/service")
    TEST_USER = "intermine-test-user"
    TEST_PASS = "intermine-test-user-password"

    # Expected rows
    KARIM = [37, '4', False, 'Karim']
    JENNIFER_SCHIRRMANN = [55, '9', False, 'Jennifer Schirrmann']
    JENNIFER = [45, '8', True, 'Jennifer']
    JEAN_MARC = [53, '0', True, 'Jean-Marc']
    VINCENT = [29, '3', True, 'Vincent']
    INA = [39, '8', True, 'Ina']
    ALEX = [43, '0', True, 'Alex']
    DELPHINE = [47, '9', False, 'Delphine']
    BRENDA = [54, '2', False, 'Brenda']
    KEITH = [56, None, False, 'Keith Bishop']
    CAROL = [62, '3', True, 'Carol']
    GARETH = [61, '8', True, 'Gareth Keenan']
    DAVID = [41, None, False, 'David Brent']
    FRANK = [44, None, False, 'Frank M\xf6llers']
    JULIETTE = [71, None, False, 'Juliette Lebrac']
    BWAH_HA = [74, None, False, "Bwa'h Ha Ha"]

    SERVICE = Service(TEST_ROOT, TEST_USER, TEST_PASS)

    LADIES_NAMES = [
        "Brenda", "Zop", "Carol", "Quux", "Jennifer", "Delphine", "Ina"
    ]
    GUYS_NAMES = 'Alex Karim "Gareth Keenan" Foo Bar "Keith Bishop" Vincent Baz'
    UNICODE_NAMES = UNICODE_NAMES

    EMPLOYEE_FILE = "tests/data/test-identifiers.list"
    TYPE = 'Employee'

    maxDiff = None

    def __init__(self, name):
        unittest.TestCase.__init__(self, name)
        self.initialListCount = self.SERVICE.get_list_count()

    # Disabled due to bug in FlyMine 34.0.
    # def testListsFromFlyMine(self):
    #     s = Service("www.flymine.org/query")
    #     all_lists = s.get_all_lists()
    #     possible_statuses = set(["CURRENT", "TO_UPGRADE", "NOT_CURRENT"])
    #     got = set((l.status for l in all_lists))
    #     self.assertTrue(got <= possible_statuses)

    # # @unittest.skip("disabled")
    def testListTagAdding(self):
        s = self.SERVICE
        t = self.TYPE
        list = s.create_list(
            self.GUYS_NAMES,
            t,
            description="Id string",
            tags=['test', 'tag-adding'])
        self.assertEqual(set(['test', 'tag-adding']), list.tags)
        list.add_tags("a-tag", "b-tag")
        self.assertEqual(
            set(['test', 'tag-adding', "a-tag", "b-tag"]), list.tags)

    # @unittest.skip("disabled")
    def testUnicode(self):
        s = self.SERVICE
        t = self.TYPE
        list = s.create_list(self.UNICODE_NAMES, t,
                             description='unicode names', tags=['test'])
        self.assertEqual(len(self.UNICODE_NAMES), list.size)

    # @unittest.skip("disabled")
    def testListTagRemoval(self):
        s = self.SERVICE
        t = self.TYPE
        tags = ["a-tag", "b-tag", "c-tag", 'test']
        list = s.create_list(self.GUYS_NAMES, t,
                             description="tag removal", tags=tags)
        self.assertEqual(set(tags), list.tags)
        list.remove_tags("a-tag", "c-tag")
        self.assertEqual(set(["b-tag", 'test']), list.tags)
        list.remove_tags("b-tag", "d-tag")
        self.assertEqual(set(['test']), list.tags)

    # @unittest.skip("disabled")
    def testListTagUpdating(self):
        s = self.SERVICE
        t = self.TYPE
        list = s.create_list(self.GUYS_NAMES, t,
                             description="tag updating", tags=['test'])
        self.assertEqual(set(['test']), list.tags)
        self.assertEqual(set(['test', "a-tag", "b-tag"]),
                         set(map(str, s._list_manager.add_tags(list, ["a-tag", "b-tag"]))))
        self.assertEqual(set(['test']), list.tags)
        list.update_tags()
        self.assertEqual(
            set(['test', "a-tag", "b-tag"]), set(map(str, list.tags)))

    def test_context_manager(self):
        t = self.TYPE
        before = self.SERVICE.get_list_count()
        tags = ['test']
        desc = 'context-manager {0}'.format

        with self.SERVICE.list_manager() as m:
            self.LOG.debug("ALL names before a: {0}".format(
                m.get_all_list_names()))
            a = m.create_list(
                self.LADIES_NAMES, t, description=desc("a"), tags=tags)
            self.assertEqual(5, a.size)

            self.LOG.debug("ALL names before b: {0}".format(
                m.get_all_list_names()))
            b = m.create_list(
                self.GUYS_NAMES, t, description=desc("b"), tags=tags)
            self.assertEqual(5, b.size)

            self.LOG.debug("ALL names before c: {0}".format(
                m.get_all_list_names()))
            c = m.create_list(
                self.EMPLOYEE_FILE, t, description=desc("c"), tags=tags)
            self.assertEqual(5, c.size)

            d = a | b | c
            self.assertEqual(14, d.size)
            self.assertEqual(before + 5, m.get_list_count())
        self.assertEqual(before, self.SERVICE.get_list_count())

    # @unittest.skip("disabled")
    def testListTagUpdating(self):
        s = self.SERVICE
        t = self.TYPE
        list = s.create_list(self.GUYS_NAMES, t,
                             description="tag updating", tags=['test'])
        self.assertEqual(set(['test']), list.tags)
        self.assertEqual(set(['test', "a-tag", "b-tag"]),
                         set(map(str, s._list_manager.add_tags(list, ["a-tag", "b-tag"]))))
        self.assertEqual(set(['test']), list.tags)
        list.update_tags()
        self.assertEqual(
            set(['test', "a-tag", "b-tag"]), set(map(str, list.tags)))

    # @unittest.skip("disabled")
    def test_ladies_names(self):
        t = self.TYPE
        s = self.SERVICE

        list = s.create_list(
            self.LADIES_NAMES,
            t,
            description="Id list",
            tags=["Foo", "Bar", "test"])
        self.assertEqual(list.unmatched_identifiers, set(["Zop", "Quux"]))
        self.assertEqual(list.size, 5)
        self.assertEqual(list.list_type, t)
        self.assertEqual(list.tags, set(["Foo", "Bar", "test"]))

        list = s.get_list(list.name)
        self.assertEqual(list.size, 5)
        self.assertEqual(list.list_type, t)

    # @unittest.skip("disabled")
    def test_guys_names(self):
        t = self.TYPE
        s = self.SERVICE

        list = s.create_list(
            self.GUYS_NAMES,
            t,
            description="Id string",
            tags=["Foo", "Bar", "test"])
        self.assertEqual(list.unmatched_identifiers,
                         set(["Foo", "Bar", "Baz"]))
        self.assertEqual(list.size, 5)
        self.assertEqual(list.list_type, "Employee")
        self.assertEqual(list.tags, set(["Foo", "Bar", "test"]))

    # @unittest.skip("disabled")
    def test_from_file(self):
        t = self.TYPE
        s = self.SERVICE

        list = s.create_list(self.EMPLOYEE_FILE, t,
                             description="Id file", tags=["Foo", "Bar", "test"])
        self.assertEqual(list.unmatched_identifiers, set(["Not a good id"]))
        self.assertEqual(list.size, 5)
        self.assertEqual(list.list_type, "Employee")
        self.assertEqual(list.tags, set(["Foo", "Bar", "test"]))

    # @unittest.skip("disabled")
    def test_from_query(self):
        t = self.TYPE
        s = self.SERVICE

        q = s.new_query()
        q.add_view("Employee.id")
        q.add_constraint("Employee.department.name", '=', "Sales")
        list = s.create_list(q, description="Id query", tags=['test'])
        self.assertEqual(list.unmatched_identifiers, set())
        self.assertEqual(list.size, 18)
        self.assertEqual(list.list_type, t)

    # @unittest.skip("disabled")
    def test_renaming(self):
        t = self.TYPE
        s = self.SERVICE

        q = s.select("Employee").where("department.name", "=", "Sales")
        list = s.create_list(q, description="test renaming",
                             tags=["test", "query"])
        old_name = list.name

        list.name = "the list previously known as {0}".format(old_name)

        l2 = s.get_list(list.name)
        self.assertEqual(str(list), str(l2))

    # @unittest.skip("disabled")
    def test_from_other_list(self):
        t = self.TYPE
        s = self.SERVICE

        q = s.select("Employee").where("department.name", "=", "Sales")
        list = s.create_list(q, description="test_from_other_list",
                             tags=["test", "query"])

        from_other = s.create_list(list)
        self.assertEqual(from_other.size, list.size)

    # @unittest.skip("disabled")
    def test_delete(self):
        t = self.TYPE
        s = self.SERVICE

        q = s.select("Employee").where("department.name", "=", "Sales")
        list = s.create_list(q, description="test_delete",
                             tags=["test", "query"])

        name = list.name
        list.delete()
        self.assertTrue(s.get_list(name) is None)

    # @unittest.skip("disabled")
    def test_to_query(self):
        t = self.TYPE
        s = self.SERVICE

        list = s.create_list(self.EMPLOYEE_FILE, t,
                             description='test_to_query', tags=['test'])
        expected = [
            LiveListTest.KARIM, LiveListTest.DAVID, LiveListTest.FRANK,
            LiveListTest.JEAN_MARC, LiveListTest.JENNIFER_SCHIRRMANN
        ]

        got = [row[:3] + row[4:] for row in l.to_query().rows()]
        self.assertEqual(got, expected)

    # @unittest.skip("disabled")
    def test_iteration(self):
        t = self.TYPE
        s = self.SERVICE

        list = s.create_list(self.EMPLOYEE_FILE, t,
                             description='test_iteration', tags=['test'])

        # Test iteration:
        got = set([x.age for x in l])
        expected_ages = set([37, 41, 44, 53, 55])
        self.assertEqual(expected_ages, got)

        self.assertTrue(list[0].age in expected_ages)
        self.assertTrue(list[-1].age in expected_ages)
        self.assertTrue(list[2].age in expected_ages)
        self.assertRaises(IndexError, lambda: list[5])
        self.assertRaises(IndexError, lambda: list[-6])
        self.assertRaises(IndexError, lambda: list["foo"])

    # @unittest.skip("disabled")
    def test_intersections(self):
        t = self.TYPE
        s = self.SERVICE

        listA = s.create_list(
            self.GUYS_NAMES,
            t,
            description='test_intersections a',
            tags=['test'])
        listB = s.create_list(
            self.EMPLOYEE_FILE,
            t,
            description='test_intersections b',
            tags=['test'])

        intersection = listA & listB
        self.assertEqual(intersection.size, 1)
        expected = [LiveListTest.KARIM]
        self.assertEqual(emp_rows_without_ids(intersection), expected)

        q = s.new_query("Employee").where("age", ">", 50)
        intersection = listB & q
        self.assertEqual(intersection.size, 2)
        expected = [LiveListTest.JEAN_MARC, LiveListTest.JENNIFER_SCHIRRMANN]
        self.assertEqual(emp_rows_without_ids(intersection), expected)

        prev_name = listA.name
        prev_desc = listA.description
        listA &= listB
        self.assertEqual(listA.size, 1)
        got = emp_rows_without_ids(listA)
        expected = [LiveListTest.KARIM]
        self.assertEqual(got, expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)

    # @unittest.skip("disabled")
    def test_unions(self):
        t = self.TYPE
        s = self.SERVICE

        listA = s.create_list(
            self.GUYS_NAMES,
            t,
            description='test_unions a',
            tags=['test', "tagA", "tagB"])
        listB = s.create_list(
            self.LADIES_NAMES, t, description='test_unions b', tags=['test'])

        union = listA | listB
        self.assertEqual(union.size, 10)
        expected = [
            LiveListTest.VINCENT, LiveListTest.KARIM, LiveListTest.INA,
            LiveListTest.ALEX, LiveListTest.JENNIFER, LiveListTest.DELPHINE,
            LiveListTest.BRENDA, LiveListTest.KEITH, LiveListTest.GARETH,
            LiveListTest.CAROL
        ]
        got = [row[:3] + row[4:] for row in union.to_query().rows()]
        self.assertEqual(got, expected)

        union = listA + listB
        self.assertEqual(union.size, 10)
        self.assertEqual(emp_rows_without_ids(union), expected)

    # @unittest.skip("disabled")
    def test_appending_list(self):
        t = self.TYPE
        s = self.SERVICE

        # Test appending
        listA = s.create_list(
            self.GUYS_NAMES,
            t,
            description='test_appending_list a',
            tags=['test', "tagA", "tagB"])
        listB = s.create_list(
            self.LADIES_NAMES,
            t,
            description='test_appending_list b',
            tags=['test'])
        expected = [
            LiveListTest.VINCENT, LiveListTest.KARIM, LiveListTest.INA,
            LiveListTest.ALEX, LiveListTest.JENNIFER, LiveListTest.DELPHINE,
            LiveListTest.BRENDA, LiveListTest.KEITH, LiveListTest.GARETH,
            LiveListTest.CAROL
        ]

        prev_name = listA.name
        prev_desc = listA.description
        listA += listB
        self.assertEqual(listA.size, 10)
        self.assertEqual(listA.tags, set(['test', "tagA", "tagB"]))
        fromService = s.get_list(listA.name)
        self.assertEqual(listA.tags, fromService.tags)
        self.assertEqual(emp_rows_without_ids(listA), expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)

    # @unittest.skip("disabled")
    def test_appending_identifiers(self):
        s = self.SERVICE
        t = self.TYPE
        expected = [
            LiveListTest.VINCENT, LiveListTest.KARIM, LiveListTest.INA,
            LiveListTest.ALEX, LiveListTest.JENNIFER, LiveListTest.DELPHINE,
            LiveListTest.BRENDA, LiveListTest.KEITH, LiveListTest.GARETH,
            LiveListTest.CAROL
        ]

        listA = s.create_list(
            self.GUYS_NAMES, t, description="testing appending", tags=['test'])
        prev_name = listA.name
        prev_desc = listA.description
        listA += self.LADIES_NAMES
        self.assertEqual(listA.size, 10)
        self.assertEqual(emp_rows_without_ids(listA), expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)
        self.assertEqual(len(listA.unmatched_identifiers), 5)

    # @unittest.skip("disabled")
    def test_appending_file(self):
        s = self.SERVICE
        t = self.TYPE

        listA = s.create_list(
            self.GUYS_NAMES,
            t,
            description="testing appending file",
            tags=['test'])
        prev_name = listA.name
        prev_desc = listA.description
        listA += self.EMPLOYEE_FILE
        self.assertEqual(listA.size, 9)
        expected = [
            LiveListTest.VINCENT, LiveListTest.KARIM, LiveListTest.DAVID,
            LiveListTest.ALEX, LiveListTest.FRANK, LiveListTest.JEAN_MARC,
            LiveListTest.JENNIFER_SCHIRRMANN, LiveListTest.KEITH,
            LiveListTest.GARETH
        ]
        self.assertEqual(emp_rows_without_ids(listA), expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)

    # @unittest.skip("disabled")
    def test_appending_collection_of_lists(self):
        s = self.SERVICE
        t = self.TYPE
        listA = s.create_list(
            self.GUYS_NAMES, t, description='appending_lists a', tags=['test'])
        listB = s.create_list(
            self.EMPLOYEE_FILE,
            t,
            description='appending_lists b',
            tags=['test'])
        listC = s.create_list(
            self.LADIES_NAMES,
            t,
            description='appending_lists c',
            tags=['test'])

        prev_name = listA.name
        prev_desc = listA.description
        listA += [listA, listB, listC]
        self.assertEqual(listA.size, 14)
        expected = [
            LiveListTest.VINCENT, LiveListTest.KARIM, LiveListTest.INA,
            LiveListTest.DAVID, LiveListTest.ALEX, LiveListTest.FRANK,
            LiveListTest.JENNIFER, LiveListTest.DELPHINE,
            LiveListTest.JEAN_MARC, LiveListTest.BRENDA,
            LiveListTest.JENNIFER_SCHIRRMANN, LiveListTest.KEITH,
            LiveListTest.GARETH, LiveListTest.CAROL
        ]
        self.assertEqual(emp_rows_without_ids(listA), expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)

    # @unittest.skip("disabled")
    def test_appending_collection_of_lists_and_queries(self):
        s = self.SERVICE
        t = self.TYPE
        listA = s.create_list(
            self.GUYS_NAMES,
            t,
            description='appending_lists_and_qs a',
            tags=['test'])
        listB = s.create_list(
            self.EMPLOYEE_FILE,
            t,
            description='appending_lists_and_qs b',
            tags=['test'])
        listC = s.create_list(
            self.LADIES_NAMES,
            t,
            description='appending_lists_and_qs c',
            tags=['test'])
        q = s.new_query()
        q.add_view("Employee.id")
        q.add_constraint("Employee.age", '>', 65)

        prev_name = listA.name
        prev_desc = listA.description
        listA += [listA, listB, listC, q]
        self.assertEqual(listA.size, 16)
        expected = [
            LiveListTest.VINCENT, LiveListTest.KARIM, LiveListTest.INA,
            LiveListTest.DAVID, LiveListTest.ALEX, LiveListTest.FRANK,
            LiveListTest.JENNIFER, LiveListTest.DELPHINE,
            LiveListTest.JEAN_MARC, LiveListTest.BRENDA,
            LiveListTest.JENNIFER_SCHIRRMANN, LiveListTest.KEITH,
            LiveListTest.GARETH, LiveListTest.CAROL, LiveListTest.JULIETTE,
            LiveListTest.BWAH_HA
        ]
        self.assertEqual(emp_rows_without_ids(listA), expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)

    # @unittest.skip("disabled")
    def test_diffing(self):
        s = self.SERVICE
        t = self.TYPE

        listA = s.create_list(
            self.GUYS_NAMES, t, description='test_diffing a', tags=['test'])
        listB = s.create_list(
            self.EMPLOYEE_FILE, t, description='test_diffing b', tags=['test'])

        diff = listA ^ listB
        self.assertEqual(diff.size, 8)
        expected = [
            LiveListTest.VINCENT, LiveListTest.DAVID, LiveListTest.ALEX,
            LiveListTest.FRANK, LiveListTest.JEAN_MARC,
            LiveListTest.JENNIFER_SCHIRRMANN, LiveListTest.KEITH,
            LiveListTest.GARETH
        ]
        self.assertEqual(emp_rows_without_ids(diff), expected)

        prev_name = listA.name
        prev_desc = listA.description
        listA ^= listB
        self.assertEqual(listA.size, 8)
        self.assertEqual(emp_rows_without_ids(listA), expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)

    # @unittest.skip("disabled")
    def test_subtraction(self):
        s = self.SERVICE
        t = self.TYPE

        listA = s.create_list(
            self.GUYS_NAMES,
            t,
            description='test_subtraction a',
            tags=["subtr-a", "subtr-b"])
        listB = s.create_list(
            self.EMPLOYEE_FILE,
            t,
            description='test_subtraction b',
            tags=['test'])

        subtr = listA - listB
        self.assertEqual(subtr.size, 4)
        expected = [
            LiveListTest.VINCENT, LiveListTest.ALEX, LiveListTest.KEITH,
            LiveListTest.GARETH
        ]
        got = [row[:3] + row[4:] for row in subtr.to_query().rows()]
        self.assertEqual(got, expected)

        prev_name = listA.name
        prev_desc = listA.description
        listA -= listB
        self.assertEqual(listA.size, 4)
        self.assertEqual(listA.tags, set(["subtr-a", "subtr-b"]))
        self.assertEqual(emp_rows_without_ids(listA), expected)
        self.assertEqual(prev_name, listA.name)
        self.assertEqual(prev_desc, listA.description)

    # @unittest.skip("disabled")
    def test_subqueries(self):
        s = self.SERVICE
        t = self.TYPE

        with_cc_q = s.model.Bank.where("corporateCustomers.id", "IS NOT NULL")
        with_cc_l = s.create_list(with_cc_q, description='test_subqueries')

        self.assertEqual(2,
                         s.model.Bank.where(s.model.Bank ^ with_cc_q).count())
        self.assertEqual(2,
                         s.model.Bank.where(s.model.Bank ^ with_cc_l).count())

        self.assertEqual(3,
                         s.model.Bank.where(s.model.Bank < with_cc_q).count())
        self.assertEqual(3,
                         s.model.Bank.where(s.model.Bank < with_cc_l).count())

        boring_q = s.new_query("Bank")
        boring_q.add_constraint("Bank", "NOT IN", with_cc_q)
        self.assertEqual(2, boring_q.count())

        boring_q = s.new_query("Bank")
        boring_q.add_constraint("Bank", "NOT IN", with_cc_l)
        self.assertEqual(2, boring_q.count())

    # @unittest.skip("disabled")
    def test_query_overloading(self):
        s = self.SERVICE
        t = self.TYPE

        with_cc_q = s.model.Bank.where('corporateCustomers.id', 'IS NOT NULL')
        with_cc_l = s.create_list(
            with_cc_q, description=['test_query_overloading'])

        no_comps = s.new_query('Bank') - with_cc_q
        self.assertEqual(2, no_comps.size)

        no_comps = s.new_query('Bank') - with_cc_l
        self.assertEqual(2, no_comps.size)

        all_b = s.new_query('Bank') | with_cc_q
        self.assertEqual(5, all_b.size)

        all_b = s.new_query('Bank') | with_cc_l
        self.assertEqual(5, all_b.size)

    # @unittest.skip("disabled")
    def test_enrichment(self):
        s = self.SERVICE
        t = self.TYPE

        favs = s.l('My-Favourite-Employees')
        enriched_contractors = [
            x.identifier
            for x in favs.calculate_enrichment(
                'contractor_enrichment', maxp=1.0)
        ]
        self.assertEqual(enriched_contractors, ['Vikram'])

    def tearDown(self):
        s = self.SERVICE
        for l in s.get_all_lists():
            if 'test' in l.tags:
                l.delete()

        s.__del__()
        self.assertEqual(self.SERVICE.get_list_count(), self.initialListCount)


class LiveListTestWithTokens(LiveListTest):
    SERVICE = Service(LiveListTest.TEST_ROOT, token="test-user-token")


if __name__ == '__main__':
    unittest.main()
