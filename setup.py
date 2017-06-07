"""
The test and clean code is shamelessly stolen from
http://da44en.wordpress.com/2002/11/22/using-distutils/
"""

from __future__ import print_function

import os
import sys
import time
import logging
from distutils.core import Command, setup
from distutils import log
from distutils.fancy_getopt import fancy_getopt
from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin
from warnings import warn

from intermine import VERSION

OPTIONS = {
    'name': "intermine",
    'packages': ["intermine", "intermine.lists"],
    'provides': ["intermine"],
    'version': VERSION,
    'description': "InterMine WebService client",
    'author': "InterMine team",
    'author_email': "all@intermine.org",
    'url': "http://www.intermine.org",
    'keywords': ["webservice", "genomic", "bioinformatics"],
    'classifiers': [
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Operating System :: OS Independent",
    ],
    'license': "LGPL, BSD",
    'long_description': """\
InterMine Webservice Client
----------------------------

A Python API to access bioinformatics data warehouses powered by the InterMine platform.

"""
}

class TestCommand(Command):
    description = "Run unit tests"
    user_options = [
        ('verbose', 'v', "produce verbose output"),
        ('testmodule=', 't', 'test module name')
    ]
    boolean_options = ['verbose']

    def initialize_options(self):
        self._dir = os.getcwd()
        self.test_prefix = 'test_'
        self.verbose = 0
        self.testmodule = None

    def finalize_options(self):
        pass

    def run(self):
        '''
        Finds all the tests modules in tests/, and runs them, exiting after they are all done
        '''
        from tests.server import TestServer
        from tests.test_core import WebserviceTest

        log.set_verbosity(self.verbose)
        if self.verbose >= 2:
            self.announce('Setting log level to DEBUG ({0})'.format(logging.DEBUG), level = 2)
            logging.basicConfig(level = logging.DEBUG)

        testfiles = [ ]
        if self.testmodule is None:
            for t in glob(pjoin(self._dir, 'tests', self.test_prefix + '*.py')):
                if not t.endswith('__init__.py'):
                    testfiles.append('.'.join(['tests', splitext(basename(t))[0]]))
        else:
            testfiles.append(self.testmodule)

        server = TestServer(daemonise = True, silent = (self.verbose < 3))
        server.start()
        WebserviceTest.TEST_PORT = server.port

        self.announce("Waiting for test server to start on port " + str(server.port), level=2)
        time.sleep(1)

        self.announce("Test files:" + str(testfiles), level=2)
        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = self.verbose)
        result = t.run(tests)
        failed, errored = map(len, (result.failures, result.errors))
        exit(failed + errored)

class PrintVersion(Command):
    user_options = []

    def initialize_options(self):
        self.version = None

    def finalize_options(self):
        self.version = OPTIONS['version']

    def run(self):
        print(self.version)

class LiveTestCommand(TestCommand):

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.test_prefix = 'live'

class CleanCommand(Command):
    """
    Remove all build files and all compiled files
    =============================================

    Remove everything from build, including that
    directory, and all .pyc files
    """
    user_options = [('verbose', 'v', "produce verbose output")]

    def initialize_options(self):
        self._files_to_delete = [ ]
        self._dirs_to_delete = [ ]

        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyc'):
                    self._files_to_delete.append(pjoin(root, f))
        for root, dirs, files in os.walk(pjoin('build')):
            for f in files:
                self._files_to_delete.append(pjoin(root, f))
            for d in dirs:
                self._dirs_to_delete.append(pjoin(root, d))
        # reverse dir list to only get empty dirs
        self._dirs_to_delete.reverse()
        self._dirs_to_delete.append('build')

        self.verbose = 0

    def finalize_options(self):
        fancy_getopt(self.user_options, {}, self, None)

    def run(self):
        for clean_me in self._files_to_delete:
            if self.dry_run:
                log.info("Would have unlinked " + clean_me)
            else:
                try:
                    self.announce("Deleting " + clean_me, level=2)
                    os.unlink(clean_me)
                except:
                    message = " ".join(["Failed to delete file", clean_me])
                    log.warn(message)
        for clean_me in self._dirs_to_delete:
            if self.dry_run:
                log.info("Would have rmdir'ed " + clean_me)
            else:
                if os.path.exists(clean_me):
                    try:
                        self.announce("Going to remove " + clean_me, level=2)
                        os.rmdir(clean_me)
                    except:
                        message = " ".join(["Failed to delete dir", clean_me])
                        log.warn(message)
                elif clean_me != "build":
                    log.warn(clean_me + " does not exist")

extra = {
    'cmdclass': {
        'clean': CleanCommand,
        'test': TestCommand,
        'livetest': LiveTestCommand,
        'version': PrintVersion
    }
}

OPTIONS.update(extra)

setup(**OPTIONS)
