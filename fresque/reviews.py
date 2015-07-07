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
from fresque.utils import is_safe_url, is_authenticated, handle_result
from fresque.gitview import get_repo_by_name, __get_file_in_tree


@APP.route('/<repo>/reviews/')
@APP.route('/<repo>/reviews')
def view_reviews(repo):
    """ List all reviews associated to a package
    """
    pass


@APP.route('/<repo>/new_review/', methods=('GET', 'POST'))
@APP.route('/<repo>/new_review', methods=('GET', 'POST'))
def new_review(repo, username=None):
    """ Create a new review
    """

    repo_obj = get_repo_by_name(repo)

    if repo_obj is None:
        flask.abort(404, 'Project not found')

    result = fresque.lib.views.new_review(
        flask.g.db, flask.request.method, flask.request.form,
        flask.g.fas_user.username, repo)

    # check here the last activity of the reviews
    return handle_result(result, '/git/new_review.html')
