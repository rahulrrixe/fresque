# -*- coding: utf-8 -*-

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


