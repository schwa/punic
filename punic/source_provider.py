
from pathlib2 import Path

class SourceProvider(object):

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
    def __init__(self, path):
        super(LocalSourceProvider.__init__, path.name, ('local;', path))
        self.path = path
