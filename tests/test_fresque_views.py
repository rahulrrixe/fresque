# -*- coding: utf-8 -*-

import pkg_resources

import unittest
import shutil
import sys
import os

import json
from mock import patch
from StringIO import StringIO

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

        output = self.app.get('/packages')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<a href="/packages/spiderman">spiderman</a>' in output.data)

    def test_package(self):
        output = self.app.get('/packages/spiderman')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<p><strong>Summary:</strong> web crawler</p>' in output.data)

    def test_package_reviews(self):
        output = self.app.get('/packages/spiderman/reviews/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<p>reviews for package spiderman</p>' in output.data)

    def test_new_package_reviews(self):
        output = self.app.get('/packages/spiderman/reviews/new')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<p>new review for package spiderman</p>' in output.data)

    def test_package_reviews_id(self):
        output = self.app.get('/packages/spiderman/reviews/1')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<p>review 1</p>' in output.data)

    def test_new_package(self):
        user = tests.FakeUser()

        # with tests.user_set(fresque.APP, user):
        #     output = self.app.get('/new')
        #     self.assertTrue('<a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">'
        #         'username <span class="caret"></span></a>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FresqueFlaskApptests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
