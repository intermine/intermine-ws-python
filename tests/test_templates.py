import unittest
import sys

from intermine.webservice import *
from intermine.query import Template
from intermine.constraints import TemplateConstraint

from tests.test_core import WebserviceTest

P3K = sys.version_info >= (3, 0)


class TestTemplates(WebserviceTest):  # pragma: no cover

    def setUp(self):
        self.service = Service(self.get_test_root())

    def testGetTemplatesLength(self):
        """Should be able to see how many templates there are"""
        self.assertEqual(len(self.service.templates), 12)

    def testGetTemplate(self):
        """Should be able to get a template from the webservice,
        if it exists, and get its results"""
        t = self.service.get_template("MultiValueConstraints")
        self.assertTrue(isinstance(t, Template))
        if P3K:
            expected = "[<TemplateMultiConstraint: Employee.name ONE OF ['Dick', 'Jane', 'Timmy, the Loyal German-Shepherd'] (editable, locked)>]"
        else:
            expected = "[<TemplateMultiConstraint: Employee.name ONE OF [u'Dick', u'Jane', u'Timmy, the Loyal German-Shepherd'] (editable, locked)>]"
        self.assertEqual(repr(list(t.editable_constraints)), expected)

    def testGetTemplateResults(self):
        """Should be able to get a template from the webservice,
        if it exists, and get its results"""
        t = self.service.get_template("MultiValueConstraints")
        expected = [['foo', 'bar', 'baz'], [
            123, 1.23, -1.23], [True, False, None]]

        def do_tests(error=None, attempts=0):
            if attempts < 5:
                try:
                    self.assertEqual(t.get_results_list("list"), expected)
                except IOError as e:
                    do_tests(e, attempts + 1)
            else:
                raise RuntimeError("Error connecting to " +
                                   self.query.service.root, error)
        do_tests()

    def testNonExistantTemplate(self):
        """Should not be able to get templates that don't exist"""
        try:
            self.service.get_template("Non_Existant")
            self.fail("No ServiceError raised by non-existant template")
        except ServiceError as ex:
            self.assertEqual(
                ex.message,
                "There is no template called 'Non_Existant' at this service")

    def testIrrelevantSO(self):
        """Should fix up bad sort orders and logic when parsing from xml"""
        model = self.service.model

        xml = '''<template name="bad_so"><query name="bad_so" model="testmodel" view="Employee.name Employee.age" sortOrder="Employee.fullTime ASC"/></template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_sort_order()), "Employee.name asc")

        xml = '''<template name="bad_so"><query name="bad_so" model="testmodel" view="Employee.name Employee.age" sortOrder="Employee.fullTime"/></template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_sort_order()), "Employee.name asc")

    def testCodesInOrder(self):
        """Should associate the right constraints with the right codes"""
        model = self.service.model

        xml = '''
          <template name="codesNotInOrder">
              <query nampe="codesNotInOrder" model="testmodel" 
              view="Employee.name Employee.age">
                <constraint path="Employee.name" op="=" value="foo" code="X"/>
                <constraint path="Employee.name" op="=" value="bar" code="Y"/>
                <constraint path="Employee.name" op="=" value="baz" code="Z"/>
              </query>
          </template>
          '''
        t = Template.from_xml(xml, model)
        v = None
        try:
            v = t.get_constraint("X").value
        except Exception:
            pass

        self.assertIsNotNone(
            v, msg="Query (%s) should have a constraint with the code 'X'" % t)
        self.assertEqual("foo", v, msg="should be the correct constraint")

    def testIrrelevantConstraintLogic(self):
        """Should fix up bad logic"""
        model = self.service.model

        xml = '''<template name="bad_cl"><query name="bad_cl" 
              model="testmodel" view="Employee.name Employee.age" 
              constraintLogic="A and B and C"/></template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_logic()), "")

        xml = '''<template name="bad_cl"><query name="bad_cl" 
              model="testmodel" view="Employee.name Employee.age" 
              constraintLogic="A and B or (D and E) and C"/></template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_logic()), "")

        xml = '''<template name="bad_cl"><query name="bad_cl" model="testmodel" view="Employee.name Employee.age" constraintLogic="A or B or (D and E) and C">
                <constraint path="Employee.name" op="IS NULL"/><constraint path="Employee.age" op="IS NOT NULL"/>
                </query>
            </template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_logic()), "A or B")

        xml = '''<template name="bad_cl"><query name="bad_cl" model="testmodel" view="Employee.name Employee.age" constraintLogic="A or B or (D and E) and C">
                <constraint path="Employee.name" op="IS NULL"/><constraint path="Employee.age" op="IS NOT NULL"/><constraint path="Employee.fullTime" op="=" value="true"/>
                </query>
            </template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_logic()), "(A or B) and C")

        xml = '''<template name="bad_cl"><query name="bad_cl" model="testmodel" view="Employee.name Employee.age" constraintLogic="A or B or (D and E) or C">
                <constraint path="Employee.name" op="IS NULL"/><constraint path="Employee.age" op="IS NOT NULL"/><constraint path="Employee.fullTime" op="=" value="true"/>
                </query>
            </template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_logic()), "A or B or C")

        xml = '''<template name="bad_cl"><query name="bad_cl" model="testmodel" view="Employee.name Employee.age" constraintLogic="A or B and (D and E) or C">
                <constraint path="Employee.name" op="IS NULL"/>
                <constraint path="Employee.age" op="IS NOT NULL"/>
                <constraint path="Employee.fullTime" op="=" value="true"/>
                </query>
            </template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_logic()), "(A or B) and C")

        xml = '''<template name="bad_cl"><query name="bad_cl" model="testmodel" view="Employee.name Employee.age" constraintLogic="A or B or (D and E) and C">
                <constraint path="Employee.name" op="IS NULL"/>
                <constraint path="Employee.age" op="IS NOT NULL"/>
                <constraint path="Employee.fullTime" op="=" value="true"/>
                <constraint path="Employee.name" op="IS NULL"/>
                </query>
            </template>'''
        t = Template.from_xml(xml, model)
        self.assertEqual(str(t.get_logic()), "(A or B or D) and C")

    def testTemplateConstraintParsing(self):
        """Should be able to parse template constraints"""
        t = self.service.get_template("UneditableConstraints")
        self.assertEqual(len(t.constraints), 2)
        self.assertEqual(len(t.editable_constraints), 1)
        expected = '[<TemplateBinaryConstraint: Company.name = Woolies (editable, locked)>]'
        self.assertEqual(expected, repr(t.editable_constraints))
        self.assertEqual(
            '<TemplateBinaryConstraint: Company.departments.name = Farm Supplies (non-editable, locked)>', repr(t.get_constraint("B")))

        t2 = self.service.get_template("SwitchableConstraints")
        self.assertEqual(len(t2.editable_constraints), 3)
        con = t2.get_constraint("A")
        self.assertTrue(con.editable and con.required and con.switched_on)
        con = t2.get_constraint("B")
        self.assertTrue(con.editable and con.optional and con.switched_on)
        self.assertEqual(
            '<TemplateBinaryConstraint: Company.departments.name = Farm Supplies (editable, on)>', repr(con))
        con.switch_off()
        self.assertTrue(con.editable and con.optional and con.switched_off)
        self.assertEqual(
            '<TemplateBinaryConstraint: Company.departments.name = Farm Supplies (editable, off)>', repr(con))
        con.switch_on()
        self.assertTrue(con.editable and con.optional and con.switched_on)
        con = t2.get_constraint("C")
        self.assertTrue(con.editable and con.optional and con.switched_off)

        self.assertRaises(
            ValueError, lambda: t2.get_constraint("A").switch_off())
        self.assertRaises(
            ValueError, lambda: t2.get_constraint("A").switch_on())

    def testBadTemplateConstraint(self):
        self.assertRaises(
            TypeError, lambda: TemplateConstraint(True, "BAD_VALUE"))
