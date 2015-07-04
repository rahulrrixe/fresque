# -*- coding: utf-8 -*-

'''
reviews for the fresque flask application
'''

from __future__ import absolute_import, unicode_literals, print_function

import os
import flask
import pygit2
import fresque

import kitchen.text.converters as ktc
import mimetypes
import chardet

from fresque import APP
from fresque.lib.git import Repository
from fresque.gitview import get_repo_by_name, __get_file_in_tree


@APP.route('/<repo>/reviews/')
@APP.route('/<repo>/reviews')
def view_issues(repo):
    """ List all reviews associated to a package
    """
    pass

