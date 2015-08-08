# -*- coding: utf-8 -*-

import pkg_resources

import unittest
import shutil
import sys
import os

import json
from mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fresque.lib
import tests


class FresqueFlaskApptests(tests.Modeltests):
    """ Tests for flask app controller of pagure """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FresqueFlaskApptests, self).setUp()

        fresque.APP.config['TESTING'] = True
        fresque.SESSION = self.session

        fresque.APP.config['GIT_DIRECTORY_PATH'] = tests.HERE
        self.app = fresque.APP.test_client()

    def test_index(self):
        """ Test the index endpoint. """

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h2>Recent activity</h2>' in output.data)

    def test_packages(self):
        tests.create_packages(self.session)
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<a href="/packages/spiderman">spiderman</a>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FresqueFlaskApptests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
