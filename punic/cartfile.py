from __future__ import division, absolute_import, print_function

__all__ = ['Cartfile']

import re
from pathlib2 import Path
from .specification import *
from .errors import *
import six

class Cartfile(object):
    def __init__(self, specifications=None, use_ssh=False, overrides=None):
        self.specifications = specifications if specifications else []
        self.use_ssh = use_ssh
        self.overrides = overrides

    def read(self, source):
        """
        >>> Cartfile().read("# This is a comment")
        []
        >>> Cartfile().read("    # This is a comment")
        []
        >>> Cartfile().read('github "schwa/SwiftUtilities" ~> 0.2.3')
        [github "schwa/SwiftUtilities" ~> 0.2.3]
        >>> Cartfile().read(['# This is a command', 'github "schwa/SwiftUtilities" ~> 0.2.3', '# This is a comment too'])
        [github "schwa/SwiftUtilities" ~> 0.2.3]
        """

        if isinstance(source, Path):
            if not source.exists():
                raise CartfileNotFound(path=source)
            source = source.open().read()

        if isinstance(source, six.string_types):
            lines = [line.rstrip() for line in source.splitlines()]

        if isinstance(source, list):
            lines = source

        # TODO: This is of course super feeble parsing. URLs with #s in them can break for example
        lines = [re.sub(r'\s*#.+', '', line) for line in lines]
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line]
        lines = [line for line in lines if line != "#"]
        self.specifications = [Specification.cartfile_string(line, use_ssh=self.use_ssh, overrides=self.overrides) for line in lines]
        return self.specifications

    def write(self, destination):
        # type: (File)
        strings = [str(specification) for specification in self.specifications]
        string = u'\n'.join(sorted(strings)) + '\n'
        destination.write(string)
