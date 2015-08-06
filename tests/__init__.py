# -*- coding: utf-8 -*-

import unittest
import shutil
import sys
import tempfile
import os

from datetime import datetime

import pygit2
from contextlib import contextmanager

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fresque
import fresque.lib
import fresque.lib.models
from fresque.lib.git import Repository

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

        item = fresque.lib.models.Distribution(
            name="Fedora 21"
        )
        self.session.add(item)

        item = fresque.lib.models.TargetDistribution(
            package_id=1,
            distribution_id=1
        )
        self.session.add(item)

        item = fresque.lib.models.Review(
            package_id=1,
            commit_id="CDE10456378",
            date_start=datetime.now(),
            date_end=datetime.now(),
            srpm_filename="spiderman_srpm",
            spec_filename="spiderman_spec"
        )
        self.session.add(item)

        item = fresque.lib.models.Reviewer(
            review_id=1,
            reviewer_name="Rahul"
        )
        self.session.add(item)

        item = fresque.lib.models.Watcher(
            package_id=1,
            watcher_name="Rahul"
        )
        self.session.add(item)

        item = fresque.lib.models.Comment(
            review_id=1,
            author="Stan",
            date=datetime.now(),
            line_number=1,
            # relevant: has the comment been replied to?
            relevant=True
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


def create_projects_git(folder, bare=False):
    """ Create some projects in the database. """
    repos = []
    for project in ['test.git', 'test2.git']:
        repo_path = os.path.join(folder, project)
        repos.append(repo_path)
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        pygit2.init_repository(repo_path, bare=bare)

    return repos


def add_content_git_repo(folder):
    """ Create some content for the specified git repo. """
    if not os.path.exists(folder):
        os.makedirs(folder)
    brepo = Repository(folder, bare=True)

    newfolder = tempfile.mkdtemp(prefix='fresque-tests')
    repo = Repository.clone_repository(folder, newfolder)

    # Create a file in that git repo
    with open(os.path.join(newfolder, 'sources'), 'w') as stream:
        stream.write('foo\n bar')
    repo.index.add('sources')
    repo.index.write()

    parents = []
    commit = None
    try:
        commit = repo.revparse_single('HEAD')
    except KeyError:
        pass
    if commit:
        parents = [commit.oid.hex]

    # Commits the files added
    tree = repo.index.write_tree()
    author = pygit2.Signature(
        'Alice Author', 'alice@authors.tld')
    committer = pygit2.Signature(
        'Cecil Committer', 'cecil@committers.tld')
    repo.create_commit(
        'refs/heads/master',  # the name of the reference to update
        author,
        committer,
        'Add sources file for testing',
        # binary string representing the tree object ID
        tree,
        # list of binary strings representing parents of the new commit
        parents,
    )

    parents = []
    commit = None
    try:
        commit = repo.revparse_single('HEAD')
    except KeyError:
        pass
    if commit:
        parents = [commit.oid.hex]

    subfolder = os.path.join('folder1', 'folder2')
    if not os.path.exists(os.path.join(newfolder, subfolder)):
        os.makedirs(os.path.join(newfolder, subfolder))
    # Create a file in that git repo
    with open(os.path.join(newfolder, subfolder, 'file'), 'w') as stream:
        stream.write('foo\n bar\nbaz')
    repo.index.add(os.path.join(subfolder, 'file'))
    repo.index.write()

    # Commits the files added
    tree = repo.index.write_tree()
    author = pygit2.Signature(
        'Alice Author', 'alice@authors.tld')
    committer = pygit2.Signature(
        'Cecil Committer', 'cecil@committers.tld')
    repo.create_commit(
        'refs/heads/master',  # the name of the reference to update
        author,
        committer,
        'Add some directory and a file for more testing',
        # binary string representing the tree object ID
        tree,
        # list of binary strings representing parents of the new commit
        parents
    )

    # Push to origin
    ori_remote = repo.remotes[0]
    master_ref = repo.lookup_reference('HEAD').resolve()
    refname = '%s:%s' % (master_ref.name, master_ref.name)

    ori_remote.push([refname])

    shutil.rmtree(newfolder)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

