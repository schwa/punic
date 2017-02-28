from __future__ import division, absolute_import, print_function

__all__ = ['SemanticVersion']

import re
from functools import total_ordering


@total_ordering
class SemanticVersion(object):

    expression = re.compile(r'^(?P<prefix>[a-z,A-Z_]+)?(?P<major>\d+)(?:\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?)?(?:-(?P<identifiers>.+))?$', re.I)

    @classmethod
    def is_semantic(cls, s):
        """
        >>> SemanticVersion.is_semantic("1.0")
        True
        >>> SemanticVersion.is_semantic("x.0")
        False
        """
        # type: (str) -> bool
        match = SemanticVersion.expression.match(s)
        return True if match else False

    def __init__(self, major, minor = 0, patch=0, identifiers=None):
        """
        >>> SemanticVersion(1, 0)
        1.0
        >>> SemanticVersion(1, 0, 0)
        1.0
        >>> SemanticVersion(1, identifiers = ['0'])
        1.0-0
        """
        assert isinstance(major, int)
        assert isinstance(minor, int)
        assert isinstance(patch, int)

        self.major = major if major else 0
        self.minor = minor if minor else 0
        self.patch = patch if patch else 0
        self.identifiers = [Identifier(identifier) for identifier in identifiers] if identifiers else []

    @property
    def _components(self):
        """
        >>> SemanticVersion(1, 2, 3)._components
        ([1, 2, 3], [])
        """
        # TODO: using a tuple breaks code
        #        return (self.major, self.minor, self.patch)
        return [self.major, self.minor, self.patch], self.identifiers

    def __repr__(self):
        components = [self.major, self.minor] + ([self.patch] if self.patch else [])
        components = [str(component) for component in components]
        repr = '.'.join(components)
        if len(self.identifiers) >= 1:
            repr += '-' + '.'.join([str(identifier) for identifier in self.identifiers])
        return repr

    def __eq__(self, other):
        """
        >>> SemanticVersion.string('1') == SemanticVersion.string('1')
        True
        >>> SemanticVersion.string('1') == SemanticVersion.string('1.0')
        True
        >>> SemanticVersion.string('1') == SemanticVersion.string('1.0.0')
        True
        >>> SemanticVersion.string('1') != SemanticVersion.string('1')
        False
        """
        return self._components[0] == other._components[0] and self._components[1] == other._components[1]

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        """
        >>> SemanticVersion.string('1') < SemanticVersion.string('2')
        True
        >>> SemanticVersion.string('1') <= SemanticVersion.string('2')
        True
        >>> SemanticVersion.string('1.1') > SemanticVersion.string('1.0')
        True
        >>> SemanticVersion.string('v5.0.0-beta6') > SemanticVersion.string('v5.0.0-beta1')
        True
        >>> SemanticVersion.string('v5.0.0-beta1') > SemanticVersion.string('v5.0.0-beta6')
        False
        >>> SemanticVersion.string('v5.0.0-10') > SemanticVersion.string('v5.0.0-2')
        True
        >>> SemanticVersion.string('v5.0.0-dummy10') > SemanticVersion.string('v5.0.0-dummy2')
        False
        >>> SemanticVersion.string('v5.0.0') > SemanticVersion.string('v5.0.0-dummy2')
        True
        """

        # The same version with no identifiers is rated higher then one with identifiers
        if self._components[0] < other._components[0]:
            return True
        elif self._components[0] == other._components[0]:
            if len(other._components[1]) == 0 and len(self._components[1]) > 0:
                return True
            elif len(self._components[1]) == 0 and len(other._components[1]) > 0:
                return False
            else:
                return self._components[1] < other._components[1]
        return False

    def __hash__(self):
        """
        >>> hash(SemanticVersion(1, 0)) == hash(SemanticVersion(1, 0))
        True
        >>> hash(SemanticVersion(1, 0)) != hash(SemanticVersion(0, 1))
        True
        """
        return hash(self.major * 1000000) ^ hash(self.minor * 10000) ^ hash(self.patch * 100)

    @classmethod
    def from_dict(cls, d):
        if set(d.keys()).issubset({'major', 'minor', 'micro', 'releaselevel', 'serial'}):
            return SemanticVersion(major=d.get('major'), minor=d.get('minor'), patch=d.get('micro'))
        else:
            raise Exception('Invalid dict')

    @classmethod
    def string(cls, s):
        # type: (str) -> SemanticVersion
        """
        >>> SemanticVersion.string('1')
        1.0
        >>> SemanticVersion.string('1.2')
        1.2
        >>> SemanticVersion.string('1.2.3')
        1.2.3
        >>> SemanticVersion.string('v5.0.0-beta6')
        5.0-beta6
        >>> SemanticVersion.string('test5.0.0-beta6')
        5.0-beta6
        >>> SemanticVersion.string('test5')
        5.0
        >>> SemanticVersion.string('garbage')
        Traceback (most recent call last):
        Exception: "garbage" not a semantic version.
        >>> SemanticVersion.string('v')
        Traceback (most recent call last):
        Exception: "v" not a semantic version.
        >>> SemanticVersion.string('')
        Traceback (most recent call last):
        Exception: "" not a semantic version.
        >>> SemanticVersion.string('sync-hackathon-2015-11-09')
        Traceback (most recent call last):
        Exception: "sync-hackathon-2015-11-09" not a semantic version.
        """
        match = SemanticVersion.expression.match(s)
        if not match:
            raise Exception('"{}" not a semantic version.'.format(s))
        d = match.groupdict()
        major = int(d['major']) if d['major'] else 0
        minor = int(d['minor']) if d['minor'] else 0
        patch = int(d['patch']) if d['patch'] else 0
        identifiers = [Identifier(identifier) for identifier in (d['identifiers'].split('.') if d['identifiers'] else [])]
        return SemanticVersion(major=major, minor=minor, patch=patch, identifiers=identifiers)

    @property
    def next_major(self):
        """
        >>> SemanticVersion.string('1.2').next_major
        2.0
        """
        # type: () -> SemanticVersion
        return SemanticVersion(major=self.major + 1, minor=0, patch=0)

    @property
    def next_minor(self):
        """
        >>> SemanticVersion.string('1.2').next_major
        2.0
        """
        # type: () -> SemanticVersion
        return SemanticVersion(major=self.major, minor=self.minor + 1, patch=0)



class Identifier(object):

    def __init__(self, value):
        if isinstance(value, Identifier):
            value = value.string_value

        self.string_value = value
        self.int_value = int(value) if represents_int(value) else None


    def __repr__(self):
        return self.string_value


    def __eq__(self, other):
        return self.string_value == other.string_value


    def __ne__(self, other):
        return not self.__eq__(other)


    def __lt__(self, other):
        if self.int_value is not None and other.int_value is not None:
            return self.int_value < other.int_value
        else:
            return self.string_value < other.string_value


    def __hash__(self):
        return hash(self.string_value)

INT_RE = re.compile(r"^[-]?\d+$")
def represents_int(s):
    return INT_RE.match(str(s)) is not None