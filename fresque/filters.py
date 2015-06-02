# -*- coding: utf-8 -*-
'''
filter for the fresque flask application
'''

from __future__ import absolute_import, unicode_literals, print_function

import arrow
import markdown
import flask

from pygments import highlight
from pygments.lexers.text import DiffLexer
from pygments.formatters import HtmlFormatter

from fresque import APP


@APP.template_filter('short')
def shorted_commit(cid):
    """Gets short version of the commit id"""
    return cid[:6]


@APP.template_filter('humanize')
def humanize_date(date):
    """ Template filter returning the last commit date of the provided repo.
    """
    return arrow.get(date).humanize()


@APP.template_filter('hasattr')
def jinja_hasattr(obj, string):
    """ Template filter checking if the provided object at the provided
    string as attribute
    """
    return hasattr(obj, string)


@APP.template_filter('format_loc')
def format_loc(loc, commit=None, filename=None, prequest=None, index=None):
    """ Template filter putting the provided lines of code into a table
    """
    if loc is None:
        return

    output = [
        '<div class="highlight">',
        '<table class="code_table">'
    ]

    comments = {}
    if prequest and not isinstance(prequest, flask.wrappers.Request):
        for com in prequest.comments:
            if commit and com.commit_id == commit \
                    and com.filename == filename:
                if com.line in comments:
                    comments[com.line].append(com)
                else:
                    comments[com.line] = [com]
    for key in comments:
        comments[key] = sorted(
            comments[key], key=lambda obj: obj.date_created)

    if not index:
        index = ''

    cnt = 1
    for line in loc.split('\n'):
        if filename and commit:
            output.append(
                '<tr><td class="cell1">'
                '<a id="%(cnt)s" href="#%(cnt)s">%(cnt_lbl)s</a></td>'
                '<td class="prc" data-row="%(cnt_lbl)s"'
                ' data-filename="%(filename)s" data-commit="%(commit)s">'
                '<p>'
                '</p>'
                '</td>' % (
                    {
                        'cnt': '%s_%s' % (index, cnt),
                        'cnt_lbl': cnt,
                        'filename': filename,
                        'commit': commit,
                    }
                )
            )
        else:
            output.append(
                '<tr><td class="cell1">'
                '<a id="%(cnt)s" href="#%(cnt)s">%(cnt_lbl)s</a></td>'
                % (
                    {
                        'cnt': '%s_%s' % (index, cnt),
                        'cnt_lbl': cnt,
                    }
                )
            )

        cnt += 1
        if not line:
            output.append(line)
            continue
        if line == '</pre></div>':
            continue
        if line.startswith('<div'):
            line = line.split('<pre style="line-height: 125%">')[1]
        output.append('<td class="cell2"><pre>%s</pre></td>' % line)
        output.append('</tr>')

        tpl_delete = '<button type="submit" name="drop_comment" ' \
            'value="%(commentid)s"' \
            'onclick="return confirm(\'Do you really want to remove' \
            ' this comment?\');"' \
            'title="Remove comment">' \
            '<span class="icon icon-remove blue"></span>' \
            '</button>'

        if cnt - 1 in comments:
            for comment in comments[cnt - 1]:

                templ_delete = ''
                if authenticated() and (
                        (comment.parent.status is True
                         and comment.user.user == flask.g.fas_user.username)
                        or is_repo_admin(comment.parent.project)):
                    templ_delete = tpl_delete % ({'commentid': comment.id})

                output.append(
                    '<tr><td></td>'
                    '<td colspan="2"><table style="width:100%%"><tr>'
                    '<td><a href="%(url)s">%(user)s</a></td>'
                    '<td class="right">'
                    '%(date)s%(templ_delete)s'
                    '</td>'
                    '</tr>'
                    '<tr><td colspan="2" class="pr_comment">%(comment)s'
                    '</td></tr>'
                    '</table></td></tr>' % (
                        {
                            'url': flask.url_for(
                                'view_user', username=comment.user.user),
                            'templ_delete': templ_delete,
                            'user': comment.user.user,
                            'date': comment.date_created.strftime(
                                '%b %d %Y %H:%M:%S'),
                            'comment': markdown_filter(comment.comment),
                        }
                    )
                )

    output.append('</table></div>')

    return '\n'.join(output)


@APP.template_filter('markdown')
def markdown_filter(text):
    """ Template filter converting a string into html content using the
    markdown library.
    """
    if text:
        # Hack to allow blockquotes to be marked by ~~~
        ntext = []
        indent = False
        for line in text.split('\n'):
            if line.startswith('~~~'):
                indent = not indent
                continue
            if indent:
                line = '    %s' % line
            ntext.append(line)
        return markdown.markdown('\n'.join(ntext))

    return ''


@APP.template_filter('html_diff')
def html_diff(diff):
    """Display diff as HTML"""
    if diff is None:
        return
    return highlight(
        diff,
        DiffLexer(),
        HtmlFormatter(
            noclasses=True,
            style="tango",)
    )


@APP.template_filter('patch_to_diff')
def patch_to_diff(patch):
    """Render a hunk as a diff"""
    content = ""
    for hunk in patch.hunks:
        content = content + "@@ -%i,%i +%i,%i @@\n" % (
            hunk.old_start, hunk.old_lines, hunk.new_start, hunk.new_lines)
        for line in hunk.lines:
            content = content + ' '.join(line)
    return content

