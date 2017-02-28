
from pathlib2 import Path

from punic.repository import *

class SourceProvider(object):

    @staticmethod
    def source_provider_with_identifier(identifier):
        if identifier.source in ('git', 'github'):
            return GitSourceProvider(identifier.name, identifier.link)
        elif identifier.source in ('local', 'root'):
            return LocalSourceProvider(identifier.name, identifier.link)
        else:
            raise Exception("Unknown source: {}".format(identifier.source))


    class Revision(object):
        pass

    def __init__(self, name, identifier):
        self.name = name
        self.identifier = identifier

    def __repr__(self):
        return str(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)


class GitSourceProvider(SourceProvider):
    def __init__(self, name, remote_url):
        super(GitSourceProvider.__init__, name, ('git', remote_url))
        self.remote_url = remote_url


class LocalSourceProvider(SourceProvider):

    class Revision(SourceProvider.Revision):
        pass

    def __init__(self, name, path):
        super(LocalSourceProvider.__init__, name, ('local;', path))
        self.path = path
