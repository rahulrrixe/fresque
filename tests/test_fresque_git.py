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
from fresque.lib.git import Repository
import tests


class FresqueGittests(tests.Modeltests):
    """ Tests for flask app controller of pagure """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FresqueGittests, self).setUp()

        fresque.APP.config['TESTING'] = True
        fresque.SESSION = self.session

        fresque.APP.config['GIT_DIRECTORY_PATH'] = tests.HERE
        self.app = fresque.APP.test_client()

    def test_repo_base_view(self):
        """ Test the index endpoint. """
        user = tests.FakeUser()

        # with tests.user_set(fresque.APP, user):
        #     output = self.app.get('/git/repo/spiderman')
        #     self.assertEqual(output.status_code, 200)
        #     # self.assertTrue('<h2>Recent activity</h2>' in output.data)

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FresqueGittests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
