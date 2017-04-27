from __future__ import division, absolute_import, print_function

__all__ = ['Specification', 'ProjectIdentifier', 'VersionOperator', 'VersionPredicate']

import functools
import re
import six
from flufl.enum import Enum
from memoize import mproperty
from pathlib2 import Path
import logging

from .semantic_version import *

# Ideally we could six.urllib but this causes problem with nosetests!
if six.PY2:
    import urlparse
elif six.PY3:
    import urllib.parse as urlparse


class Specification(object):
    def __init__(self, identifier, predicate = None):
        # type: (str, VersionPredicate)
        self.identifier = identifier
        self.predicate = predicate
        self.raw_string = None

    @classmethod
    def cartfile_string(cls, string, use_ssh=False, overrides=None):
        # type: (str) -> Specification
        """
        >>> Specification.cartfile_string('github "foo/bar"')
        github "foo/bar"
        >>> Specification.cartfile_string('github "foo/bar" "master"').identifier
        foo/bar
        >>> Specification.cartfile_string('github "foo/bar" "master"').predicate
        "master"
        >>> Specification.cartfile_string('github "foo/bar" "master"')
        github "foo/bar" "master"
        >>> Specification.cartfile_string('github "foo/bar" >= 1.0').predicate
        >= 1.0
        >>> Specification.cartfile_string('github "ReactiveX/RxSwift" "some/branch"').identifier
        ReactiveX/RxSwift
        >>> Specification.cartfile_string('github "ReactiveX/RxSwift" "some/branch"').predicate
        "some/branch"
        >>> Specification.cartfile_string('git "file:///Users/example/Project" "some/branch"').identifier
        Project
        >>> Specification.cartfile_string('git "git@gitlab.com:mokagio/punic-cartfile-issue.git" "master"').identifier
        punic-cartfile-issue
        """

        match = re.match(r'^(?P<address>(?P<service>github|git)\s+"[^/]+/(?:.+?)")(?:\s+(?P<predicate>.+)?)?', string)
        if not match:
            raise Exception('Bad spec {}'.format(string))

        identifier = ProjectIdentifier.string(match.group('address'), use_ssh=use_ssh, overrides=overrides)
        predicate = VersionPredicate(match.group('predicate'))
        specification = Specification(identifier=identifier, predicate=predicate)
        specification.raw_string = string

        return specification

    def __repr__(self):
        parts = [self.identifier.full_identifier]
        if self.predicate:
            parts += [str(self.predicate)]
        parts = [part for part in parts if part]
        return ' '.join(parts)


@functools.total_ordering
class ProjectIdentifier(object):
    @classmethod
    def string(cls, string, use_ssh=False, overrides=None):
        # type: (str) -> ProjectIdentifier
        """
        >>> ProjectIdentifier.string('github "foo/bar"')
        foo/bar
        >>> ProjectIdentifier.string('github "foo/bar"').team_name
        'foo'
        >>> ProjectIdentifier.string('github "foo/bar"').project_name
        'bar'
        >>> ProjectIdentifier.string('github "foo/bar"').identifier
        'foo/bar'
        >>> ProjectIdentifier.string('github "foo/bar"').full_identifier
        'github "foo/bar"'
        >>> ProjectIdentifier.string('github "https://github.enterprise.com/foo/bar"').team_name
        'foo'
        >>> ProjectIdentifier.string('github "https://github.enterprise.com/foo/bar"').project_name
        'bar'
        >>> ProjectIdentifier.string('github "https://github.enterprise.com/foo/bar.git"').project_name
        'bar'
        >>> ProjectIdentifier.string('github "https://github.enterprise.com/foo/bar.git"').remote_url
        'https://github.enterprise.com/foo/bar.git'
        >>> ProjectIdentifier.string('git "file:///Users/example/Projects/Example-Project"')
        Example-Project
        >>> ProjectIdentifier.string('git "git@gitlab.com:mokagio/punic-cartfile-issue.git"')
        punic-cartfile-issue
        """

        assert isinstance(string, six.string_types)
        assert isinstance(use_ssh, bool)

        match = re.match(r'^(?P<source>github|git)\s+"(?P<link>.+)"', string)
        if not match:
            raise Exception('No match')

        source = match.group('source')
        link = match.group('link')

        if source == 'github':
            match = re.match(r'(?P<remote_url>(?:.*?)(?:/|:))*(?P<team_name>[^/]+)/(?P<project_name>[^/]+?)(?:\.git)?$', link)
            if not match:
                raise Exception('No match')
            team_name = match.group('team_name')
            project_name = match.group('project_name')
            remote_url = match.group('remote_url') or 'github.com/'

            scheme = 'git@' if use_ssh else 'https://'
            remote_url = '{}{}{}/{}.git'.format(scheme, remote_url, team_name, project_name)
        elif source == 'git':
            team_name = None
            url_parts = urlparse.urlparse(link)
            path = Path(url_parts.path)
            project_name = path.stem
            remote_url = link
        else:
            raise Exception('No match')

        return ProjectIdentifier(source=source, remote_url=remote_url, team_name=team_name, project_name=project_name,
            overrides=overrides)

    def __init__(self, source=None, team_name=None, project_name=None, remote_url=None, overrides=None):
        self.source = source
        self.team_name = team_name
        self.project_name = project_name
        self.remote_url = remote_url
        if overrides and self.project_name in overrides:
            override_url = overrides[self.project_name]
            logging.info('Overriding {} with git URL {}'.format(self.project_name, override_url))
            self.remote_url = override_url

    @mproperty
    def full_identifier(self):
        if self.source == 'git':
            return '{} "{}"'.format(self.source, self.remote_url)
        elif self.source == 'github':
            return '{} "{}/{}"'.format(self.source, self.team_name, self.project_name)
        else:
            raise Exception("Unknown source")

    @mproperty
    def identifier(self):
        components = [] \
                     + ([self.team_name] if self.team_name else []) \
                     + [self.project_name]
        return '/'.join(components)

    def __repr__(self):
        return self.identifier

    def __eq__(self, other):
        """
        >>> ProjectIdentifier.string('github "foo/bar"') == ProjectIdentifier.string('github "foo/bar"')
        True
        """
        return self.identifier.lower() == other.identifier.lower()

    def __ne__(self, other):
        """
        >>> ProjectIdentifier.string('github "foo/bar"') != ProjectIdentifier.string('github "foo/bar2"')
        True
        """
        return not (self == other)

    def __lt__(self, other):
        """
        >>> ProjectIdentifier.string('github "foo/bar"') < ProjectIdentifier.string('github "foo/bar2"')
        True
        """
        return self.identifier.lower() < other.identifier.lower()

    def __hash__(self):
        """
        >>> hash(ProjectIdentifier.string('github "foo/bar"')) == hash(ProjectIdentifier.string('github "foo/bar"'))
        True
        >>> hash(ProjectIdentifier.string('github "foo/bar"')) != hash(ProjectIdentifier.string('github "foo/bar2"'))
        True
        """
        return hash(self.identifier.lower())

    def matches(self, name_filter):
        # type: ([str]) -> bool

        if not name_filter:
            return True

        if self.project_name in name_filter:
            return True

        return False


class VersionOperator(Enum):
    commitish = 'commit-ish'
    any = '<any>'
    greater_than_or_equals = '>='
    equals = '=='
    semantic_greater_than_or_equals = '~>'


class VersionPredicate(object):
    def __init__(self, string):
        """
        >>> VersionPredicate('"master"')
        "master"
        >>> VersionPredicate('>= 1.0')
        >= 1.0
        >>> VersionPredicate('~> 1.0')
        ~> 1.0
        >>> VersionPredicate('== 1.0')
        == 1.0
        """

        if not string:
            self.operator = VersionOperator.any
            self.value = None
        else:
            match = re.match(r'(?:(~>|>=|==|)\s+)?(?:"(.+)"|(.+))', string)
            if not match:
                raise Exception('No match for: {}'.format(string))

            operator = match.group(1)
            value = match.group(2) if match.group(2) else match.group(3)

            if operator == '==':
                self.operator = VersionOperator.equals
                self.value = SemanticVersion.string(value)
            elif operator == '>=':
                self.operator = VersionOperator.greater_than_or_equals
                self.value = SemanticVersion.string(value)
            elif operator == '~>':
                self.operator = VersionOperator.semantic_greater_than_or_equals
                self.value = SemanticVersion.string(value)
            else:
                self.operator = VersionOperator.commitish
                self.value = value

    def __repr__(self):
        if self.operator == VersionOperator.any:
            return ''
        if self.operator == VersionOperator.commitish:
            return '"{}"'.format(self.value)
        elif self.operator == VersionOperator.equals:
            return '== {}'.format(self.value)
        elif self.operator == VersionOperator.greater_than_or_equals:
            return '>= {}'.format(self.value)
        elif self.operator == VersionOperator.semantic_greater_than_or_equals:
            return '~> {}'.format(self.value)

    def test(self, version):
        """
        >>> VersionPredicate('== 1.0').test(SemanticVersion.string('1.0'))
        True
        >>> VersionPredicate('== 1.0').test(SemanticVersion.string('1.1'))
        False
        >>> VersionPredicate('>= 1.0').test(SemanticVersion.string('1.1'))
        True
        >>> VersionPredicate('>= 1.1').test(SemanticVersion.string('1.0'))
        False
        >>> VersionPredicate('~> 1.0').test(SemanticVersion.string('1.0'))
        True
        >>> VersionPredicate('~> 1.0').test(SemanticVersion.string('0.9'))
        False
        >>> VersionPredicate('~> 1.0').test(SemanticVersion.string('1.0.1'))
        True
        >>> VersionPredicate('~> 1.0').test(SemanticVersion.string('1.1'))
        False
        >>> VersionPredicate('~> 1.0').test(SemanticVersion.string('2.0'))
        False
        """

        # type: (SemanticVersion) -> bool
        if self.operator == VersionOperator.any:
            return True
        elif self.operator == VersionOperator.equals:
            return version == self.value
        elif self.operator == VersionOperator.greater_than_or_equals:
            return version >= self.value
        elif self.operator == VersionOperator.semantic_greater_than_or_equals:
            return self.value <= version < self.value.next_minor
        return False
