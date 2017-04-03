
from pathlib2 import Path

from punic.repository import *
from punic.errors import *
from punic.config import config

def unimplemented():
    raise PunicException("Unimplemented")

class SourceProvider(object):

    @staticmethod
    def source_provider_with_identifier(identifier):
        if identifier.source in ('git', 'github'):
            return GitSourceProvider(identifier)
        elif identifier.source in ('local', 'root'):
            return LocalSourceProvider(identifier)
        else:
            raise PunicException("Unknown source: {}".format(identifier.source))


    class Revision(object):
        pass

    def __init__(self, identifier):
        self.identifier = identifier

    def __repr__(self):
        return str(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    def revisions_for_predicate(self, predicate):
        unimplemented()


class GitSourceProvider(SourceProvider):
    def __init__(self, identifier):
        super(GitSourceProvider, self).__init__(identifier)
        self.remote_url = identifier.link
        self._repository = Repository(identifier = identifier)

    def revisions_for_predicate(self, predicate):
        return self._repository.revisions_for_predicate(predicate)

    def specifications_for_revision(self, revision):
        return self._repository.specifications_for_revision(revision)

    def fetch(self):
        return self._repository.fetch()



class LocalSourceProvider(SourceProvider):

    class Revision(SourceProvider.Revision):
        pass

    def __init__(self, identifier):
        super(LocalSourceProvider, self).__init__(identifier)
        self.path = Path(identifier.link)
