__all__ = ['GitHub']

import shlex
import subprocess

import requests
import six
# from prettytable import PrettyTable
from jsonpath_rw import parse
# import csv
# import iso8601
# import sys
# import re
from memoize import mproperty


def value(path, json):
    path = parse(path)
    result = path.find(json)
    return result[0].value if result else None

def to_string(o):
    if o is None:
        return ''
    else:
        return str(o)



class GitHub(object):

    def __init__(self):
        self.verbose = False

    @mproperty
    def auth(self):
        try:
            github_user = six.text_type(subprocess.check_output(shlex.split('git config --get github.user')).strip(), 'utf-8')
            github_token = six.text_type(subprocess.check_output(shlex.split('git config --get github.token')).strip(), 'utf-8')
        except subprocess.CalledProcessError:
            return None
        return github_user, github_token

    def search(self, name, language = 'swift'):
        q = '{} language:{} in:name fork:false'.format(name, language)
        headers = {'Accept': 'application/vnd.github.drax-preview+json'}
        r = requests.get('https://api.github.com/search/repositories?q={}&sort=stars'.format(q), auth = self.auth, headers = headers)
        items = r.json()['items']

        repositories = [GithubRepository(github=self, json=item) for item in items]

        return repositories

class GithubRepository(object):

    def __init__(self, github, json):
        self.github = github
        self.json = json
        self.full_name = self.json['full_name']
        self.name = self.json['name']
        self.owner = value('owner.login', self.json)
        self.stargazers_count = self.json['stargazers_count']

    @mproperty
    def license(self):
        headers = {'Accept': 'application/vnd.github.drax-preview+json'}
        r = requests.get('https://api.github.com/repos/{}'.format(self.full_name), auth=self.github.auth, headers=headers)
        return value('license.name', r.json())

    def __repr__(self):
        return self.full_name

# r = requests.get('https://api.github.com/repos/{}/git/refs/tags'.format(first_item['full_name']))
#
# matches = [re.match(r'^refs/tags/(.*)$', row['ref']) for row in r.json()]
# tags = [match.groups()[0] for match in matches if match]
# print(tags)
#
#
#
# sys.exit()
#
#
# r = requests.get('https://api.github.com/repos/schwa/SwiftGraphics/issues', auth=('schwa', ''))
#
# json = r.json()
#
# # writer = csv.writer(open('/Users/schwa/Desktop/issues.csv', 'w'))
# # table = PrettyTable(['Number', 'State', 'Assignee', 'Title'])
#
#
#
# class Issue(object):
#     def __init__(self, json):
#         self.json = json
#
#         self.number = json['number']
#         self.state = json['state']
#         self.title = json['title']
#         self.assignee = value('assignee.login', json)
#         self.body = json['body']
#         self.created = iso8601.parse_date(json['created_at'])
#         self.user = value('user.login', json)
#
#     def markdown(self):
#         d = self.__dict__
#         lines = []
#         lines += ['# {title} (Issue: #{number})'.format(**d), '']
#         lines += ['## Metadata', '']
#         lines += ['State', ':\t{state}'.format(**d), '']
#         lines += ['Created At', ':\t{created}'.format(**d), '']
#         lines += ['Created By', ':\t@{user}'.format(**d), '']
#         if self.assignee:
#             lines += ['Assignee', ':\t@{assignee}'.format(**d)]
#
#         if self.body:
#             lines += ['']
#             lines += ['## Body', '']
#             lines += [self.body]
#
#         return '\n'.join(lines)
#
# issues = [Issue(row) for row in json]
#
# for issue in issues:
#     print(issue.markdown())
#     print()
#     print('*' * 80)
#     print()
#
# #pprint(json[1])
