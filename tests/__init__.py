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


# pylint: disable=R0903
class FakeUser(object):
    """ Fake user used to test the fedocallib library. """

    def __init__(self, username='username'):
        self.username = username
        self.name = username
        self.email = 'foo@bar.com'
        self.dic = {}
        self.dic['timezone'] = 'Europe/Paris'
        self.login_time = datetime.utcnow()

    def __getitem__(self, key):
        return self.dic[key]


def create_packages(session):
    """ Create some projects in the database. """
    item = fresque.lib.models.Package(
        name="test 1",
        summary="A sample project for the fresque test",
        description="A python application combined with other recepies",
        owner="Sam",
        state="new",
        submitted=datetime.now(),
    )
    session.add(item)

    item = fresque.lib.models.Package(
        name="test 2",
        summary="A sample project for the fresque test",
        description="A python application combined with other recepies",
        owner="Altman",
        state="new",
        submitted=datetime.now()
    )
    session.add(item)

    session.commit()


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
    repo = pygit2.clone_repository(folder, newfolder)

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


def add_commit_git_repo(folder, ncommits=10):
    """ Create some more commits for the specified git repo. """
    if not os.path.exists(folder):
        os.makedirs(folder)
    brepo = Repository(folder, bare=True)

    newfolder = tempfile.mkdtemp(prefix='fresque-tests')
    repo = pygit2.clone_repository(folder, newfolder)

    for index in range(ncommits):
        # Create a file in that git repo
        with open(os.path.join(newfolder, 'sources'), 'a') as stream:
            stream.write('Row %s\n' % index)
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
            'Add row %s to sources file' % index,
            # binary string representing the tree object ID
            tree,
            # list of binary strings representing parents of the new commit
            parents,
        )

    # Push to origin
    ori_remote = repo.remotes[0]
    master_ref = repo.lookup_reference('HEAD').resolve()
    refname = '%s:%s' % (master_ref.name, master_ref.name)

    ori_remote.push([refname])

    shutil.rmtree(newfolder)


def add_binary_git_repo(folder, filename):
    """ Create a fake image file for the specified git repo. """
    if not os.path.exists(folder):
        os.makedirs(folder)
    brepo = Repository(folder, bare=True)

    newfolder = tempfile.mkdtemp(prefix='fresque-tests')
    repo = pygit2.clone_repository(folder, newfolder)

    content = """<89>PNG^M
^Z
^@^@^@^MIHDR^@^@^@K^@^@^@K^H^F^@^@^@8Nzê^@^@^@^FbKGD^@ÿ^@ÿ^@ÿ ½§<93>^@^@^@  pHYs^@^@^M×^@^@^M×^AB(<9b>x^@^@^@^GtIM
E^GÞ
^N^U^F^[<88>]·<9c>^@^@  <8a>IDATxÚí<9c>ÛO^Tg^_Ç?3³»ì^B
<8b>®ËË<8b>X^NÕõ^EQÚ^Z­^Qc<82>^Pk5Úô¦iMÄ^[{×^K<9b>&^^Xÿ^A<8d>WM^S^SmÒ<8b>j¯Zê<8d>   6^QO^Dª¶´/Ö^M^T5^^*¼¬<9c>^Oî<8
1><99>÷<82>Y<8b>03;3»<83>hù&d óìÃÌw~§çûüf`^Q<8b>XÄ"^V±<88>^?:<84>^Er^N^R ª¿^K3ÎK<99>ñ3^EÈêïÿ8²ò<81> <90>¥C^T^Z<84>
É@^Tè^E<86>_g²²<80>^\<95>$^?<86>æ^\TI^[SI|åÉ^R<81>Õ*QNb^\èVÝõ<95>#Ë^M^T^C^Eóì-<83>ÀC þ*<90>%^B+<80>^?¿äÄñ^XèÏ¤¥e<9
a>,^O°^Vp-<90>l<9f>^@Â<99><8a>gR^FOÌ^O<84>TËZ(HZù3õ'íÉ2<81>^R Ìé+oll¤½½<9d>þþ~^TEAQ^T"<91>^HW¯^åèÑ£¸\º^F]^F¬|Ùn(^@
å@<9e>S^DíÚµ<8b>cÇ<8e>±iÓ¦<94>cãñ8Ç<8f>^_§©©<89>^[7nh^M^Y^Fþ|YdU8ET0^X¤©©<89>Í<9b>7[þî^W_|ÁÄÄ^DçÏ<9f>çÑ£G^Y#,<9d><
98>µ^RXæ^DQõõõ´¶¶RVfÏ³ÇÇÇyøð!<95><95><95>dggsïÞ½<99><87>½j^B^Z<99>¯<98>åW^CgÆ±sçN<9a><9b><9b>ÉÎÎ¶=G<þw<89>µaÃ^F^Z^
Z^Zf^OYag^UaÇ²<jÖË86nÜÈåË<97>§ã<83>`?B<9c>9sæï<85>¥¢^P^L^Fµ,Ì^O^LX©Ã$^[<96>XéTyðË/¿<90><9b><9b>kûûCCC<9c>:u<8a>ÁÁÁ
^WÈN^RöøñcFF^ð¾^B bVÉ°Z<^F<9c>*8¿ùæ^[<82>Á á<98>X,FKK^K'O<9e>äâÅ<8b>È²LAA^A[·n¥¸¸^XA^Pp»ÝºV¹wï^¾üòËÙ×^_PU<8c><8c>f
C7Pí^DQeee<84>ÃaÜn·î<98><9e><9e>^^¶oß®<95>Ý¦M^^T©®®¦®®<8e>©©)Ý1×¯_§½½}ö¡ßÍ¬%­¸S±SµÔ<9e>={^L<89>úé§<9f>¨¨¨Ð%
"""

    parents = []
    commit = None
    try:
        commit = repo.revparse_single('HEAD')
    except KeyError:
        pass
    if commit:
        parents = [commit.oid.hex]

    # Create a file in that git repo
    with open(os.path.join(newfolder, filename), 'w') as stream:
        stream.write(content)
    repo.index.add(filename)
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
        'Add a fake image file',
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

