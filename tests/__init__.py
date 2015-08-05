# -*- coding: utf-8 -*-

"""
 (c) 2015 - Copyright Red Hat Inc
 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
"""

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import shutil
import sys
import tempfile
import os

from datetime import date
from datetime import datetime
from datetime import timedelta
from functools import wraps

import pygit2

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fresque
import fresque.lib
import fresque.lib.models
from pagure.lib.git import Repository

DB_PATH = 'sqlite:///:memory:'
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)))

@contextmanager
def user_set(APP, user):
    """ Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask.ext.fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    from flask import appcontext_pushed, g
    APP.before_request_funcs[None] = []

    def handler(sender, **kwargs):
        g.fas_user = user
        g.fas_session_id = b'123'

    with appcontext_pushed.connected_to(handler, APP):
        yield


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None
        self.path = tempfile.mkdtemp(prefix='fresque-tests')
        self.gitrepo = None
        self.gitrepos = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        # Clean up eventual git repo left in the present folder.
        for filename in os.listdir(HERE):
            filename = os.path.join(HERE, filename)
            if filename.endswith('.git') and os.path.isdir(filename):
                shutil.rmtree(filename)

        for folder in ['repos']:
            folder = os.path.join(HERE, folder)
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.mkdir(folder)

        self.session = fresque.lib.database.create_session(DB_PATH)

        # Create a couple of users
        item = fresque.lib.models.Package(
            name="Spiderman",
            summary="A sample project for the fresque test",
            description="A python application combined with other recepies",
            owner="Rahul Ranjan",
            state="new",
            submitted=datetime.now()
        )
        self.session.add(item)

        self.session.commit()

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        self.session.close()

        # Clear temp directory
        shutil.rmtree(self.path)

        # Clear DB
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
