# -*- coding: utf-8 -*-

'''
package for the fresque flask application
'''

from __future__ import absolute_import, unicode_literals, print_function

import os
import flask
import pygit2

from fresque.forms import RequestPullForm
from fresque import APP
from fresque.lib.git import Repository


@APP.route("/tree")
def show_tree():
    return flask.render_template('/git/commit.html',)


@APP.route("/repo/<name>")
def repo_base_view(name):
    path = os.path.join(
        APP.config['GIT_DIRECTORY_PATH'], flask.g.fas_user.username)

    try:
        repo_obj = Repository(os.path.join(path, name))
    except IOError:
        return "No such repo", 404

    cnt = 0
    last_commits = []
    tree = []
    if not repo_obj.is_empty:
        try:
            for commit in repo_obj.walk(
                    repo_obj.head.target, pygit2.GIT_SORT_TIME):
                last_commits.append(commit)
                cnt += 1
                if cnt == 3:
                    break
            tree = sorted(last_commits[0].tree, key=lambda x: x.filemode)
        except pygit2.GitError:
            pass
    return flask.render_template('/git/repo.html', tree=tree)


@APP.route('/<repo>/tree/')
@APP.route('/<repo>/tree/<identifier>')
def view_tree(repo, identifier=None):
    """ Render the tree of the repo
    """
    path = os.path.join(
        APP.config['GIT_DIRECTORY_PATH'], flask.g.fas_user.username)

    try:
        repo_obj = Repository(os.path.join(path, repo))
    except IOError:
        return "No such repo", 404

    if repo is None:
        flask.abort(404, 'Project not found')

    branchname = None
    content = None
    output_type = None
    if not repo_obj.is_empty:
        if identifier in repo_obj.listall_branches():
            branchname = identifier
            branch = repo_obj.lookup_branch(identifier)
            commit = branch.get_object()
        else:
            try:
                commit = repo_obj.get(identifier)
                branchname = identifier
            except (ValueError, TypeError):
                # If it's not a commit id then it's part of the filename
                commit = repo_obj[repo_obj.head.target]
                branchname = 'master'

        content = sorted(commit.tree, key=lambda x: x.filemode)
        output_type = 'tree'

    return flask.render_template(
        'file.html',
        select='tree',
        repo_obj=repo_obj,
        repo=repo,
        username=flask.g.fas_user.username,
        branchname=branchname,
        filename='',
        content=content,
        output_type=output_type,
    )


@APP.route('/<repo>/diff/<branch_to>..<branch_from>',
           methods=('GET', 'POST'))
@APP.route('/fork/<username>/<repo>/diff/<branch_to>..<branch_from>',
           methods=('GET', 'POST'))
def new_request_pull(repo, branch_to, branch_from):
    """ Request pulling the changes from the fork into the project.
    """

    path = os.path.join(
        APP.config['GIT_DIRECTORY_PATH'], flask.g.fas_user.username)

    try:
        repo_obj = Repository(os.path.join(path, repo))
        orig_repo = Repository(os.path.join(path, repo))
    except IOError:
        return "No such repo", 404

    frombranch = repo_obj.lookup_branch(branch_from)
    if not frombranch:
        flask.abort(
            400,
            'Branch %s does not exist' % branch_from)

    branch = orig_repo.lookup_branch(branch_to)
    if not branch:
        flask.abort(
            400,
            'Branch %s could not be found in the target repo' % branch_to)

    branch = repo_obj.lookup_branch(branch_from)
    commitid = branch.get_object().hex

    diff_commits = []
    if not repo_obj.is_empty and not orig_repo.is_empty:
        orig_commit = orig_repo[
            orig_repo.lookup_branch(branch_to).get_object().hex]

        master_commits = [
            commit.oid.hex
            for commit in orig_repo.walk(
                orig_commit.oid.hex, pygit2.GIT_SORT_TIME)
        ]

        repo_commit = repo_obj[commitid]

        for commit in repo_obj.walk(
                repo_commit.oid.hex, pygit2.GIT_SORT_TIME):
            if commit.oid.hex in master_commits:
                break
            diff_commits.append(commit)

        first_commit = repo_obj[diff_commits[-1].oid.hex]
        diff = repo_obj.diff(
            repo_obj.revparse_single(first_commit.parents[0].oid.hex),
            repo_obj.revparse_single(diff_commits[0].oid.hex)
        )

    elif orig_repo.is_empty:
        orig_commit = None
        repo_commit = repo_obj[repo_obj.head.target]
        diff = repo_commit.tree.diff_to_tree(swap=True)
    else:
        flask.flash(
            'Fork is empty, there are no commits to request pulling',
            'error')
        return flask.redirect(flask.url_for(
            'view_repo', username=flask.g.fas_user.username, repo=repo.name))

    print(diff.patch)

    # TODO Save patch into db for merging later on
    form = RequestPullForm()
    if form.validate_on_submit():
        print("Saved into db")

    return flask.render_template(
        '/git/pull_request.html',
        repo=repo,
        username=flask.g.fas_user.username,
        repo_obj=repo_obj,
        orig_repo=orig_repo,
        form=form,
        diff_commits=diff_commits,
        diff=diff,
        branches=[
            branch.replace('refs/heads/', '')
            for branch in sorted(orig_repo.listall_references())
        ],
        branch_to=branch_to,
        branch_from=branch_from,
    )
