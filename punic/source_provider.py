
from pathlib2 import Path

from .repository import *
from .errors import *
from .config import config
from .specification import *
import logging
import punic.shshutil as shutil
from .runner import *
from .config import *

def unimplemented():
    raise PunicException("Unimplemented")

class SourceProvider(object):

    @staticmethod
    def source_provider_with_identifier(session, identifier):
        """
        >>> SourceProvider.source_provider_with_identifier(None, ProjectIdentifier.string('github "foo/bar"'))
        GitSourceProvider('github "foo/bar"')
        >>> SourceProvider.source_provider_with_identifier(None, ProjectIdentifier.string('local "~/Project"'))
        LocalSourceProvider('~/Project')
        """
        if identifier.source in ('git', 'github'):
            return GitSourceProvider(session, identifier)
        elif identifier.source in ('local', 'root'):
            return LocalSourceProvider(session, identifier)
        else:
            raise PunicException("Unknown source: {}".format(identifier.source))

    def __init__(self, session, identifier):
        self.session = session
        self.identifier = identifier

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, str(self.identifier))

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    def fetch(self):
        unimplemented()

    def checkout(self, revision):
        unimplemented()

    def revisions_for_predicate(self, predicate):
        unimplemented()

    def specifications_for_revision(self, revision):
        unimplemented()

    def revision_for_name(self, name, check = True):
        unimplemented()

    def canonical_name_for_revision(self, revision):
        return str(revision)

    def predicate_for_revision(self, revision):
        return unimplemented()

class GitSourceProvider(SourceProvider):

    # TODO: Merge with repo? Rename to "GitRepositorySourceProvider"

    def __init__(self, session, identifier):
        super(GitSourceProvider, self).__init__(session, identifier)
        self.remote_url = identifier.link
        self._repository = Repository(identifier = identifier)

    def fetch(self):
        return self._repository.fetch()

    def checkout(self, revision):

        # TODO: Shoudl get this from a checkout object!
        checkout_path = config.checkouts_path / self._repository.identifier.project_name

        if config.use_submodules:
            relative_checkout_path = checkout_path.relative_to(config.root_path)

            result = runner.run('git submodule status "{}"'.format(relative_checkout_path))
            if result.return_code == 0:
                match = re.match(r'^(?P<flag> |-|\+|U)(?P<sha>[a-f0-9]+) (?P<path>.+)( \((?P<description>.+)\))?', result.stdout)
                flag = match.groupdict()['flag']
                if flag == ' ':
                    pass
                elif flag == '-':
                    raise PunicException('Uninitialized submodule {}. Please report this!'.format(self.checkout_path))
                elif flag == '+':
                    raise PunicException('Submodule {} doesn\'t match expected revision'.format(self.checkout_path))
                elif flag == 'U':
                    raise PunicException('Submodule {} has merge conflicts'.format(self.checkout_path))
            else:
                if checkout_path.exists():
                    raise PunicException('Want to create a submodule in {} but something already exists in there.'.format(self.checkout_path))
                logging.debug('Adding submodule for {}'.format(self))
                runner.check_run(['git', 'submodule', 'add', '--force', self.identifier.remote_url, self.checkout_path.relative_to(config.root_path)])

            # runner.check_run(['git', 'submodule', 'add', '--force', self.identifier.remote_url, self.checkout_path.relative_to(config.root_path)])
            # runner.check_run(['git', 'submodule', 'update', self.checkout_path.relative_to(config.root_path)])

            logging.debug('Updating {}'.format(self))
            self._repository.checkout(revision)
        else:

            # TODO: This isn't really 'fetch'
            if config.fetch:
                self._repository.checkout(revision)

        logging.debug('<sub>Copying project to <ref>Carthage/Checkouts</ref></sub>')
        if checkout_path.exists():
            shutil.rmtree(checkout_path, ignore_errors=True)
        shutil.copytree(self._repository.path, checkout_path, symlinks=True, ignore=shutil.ignore_patterns('.git'))

    def revisions_for_predicate(self, predicate):
        return self._repository.revisions_for_predicate(predicate)

    def specifications_for_revision(self, revision):
        return self._repository.specifications_for_revision(revision)

    def revision_for_name(self, name, check = True):
        return Revision(repository=self._repository, revision=name, revision_type=Revision.Type.commitish, check = check)

    def canonical_name_for_revision(self, revision):
        return self._repository.rev_parse(revision)

    def predicate_for_revision(self, revision):
        return VersionPredicate('"{}"'.format(revision.revision))


class LocalSourceProvider(SourceProvider):

    revision = "."

    def __init__(self, session, identifier):
        super(LocalSourceProvider, self).__init__(session,identifier)
        self.path = Path(identifier.link)

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.path)

    def fetch(self):
        # TODO: This should not copy to checkouts dir
        destination = config.checkouts_path / self.path.stem

        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(self.path, destination)

    def checkout(self, revision):
        # TODO: Not quite the same.
        self.fetch()

    def revisions_for_predicate(self, predicate):
        logging.debug(predicate)
        return [LocalSourceProvider.revision]

    def specifications_for_revision(self, revision):
        if revision == LocalSourceProvider.revision:
            return []
        else:
            return [Specification(identifier=self.identifier)]

    def revision_for_name(self, name, check = True):
        if name != LocalSourceProvider.revision:
            raise PunicException("Name mismatch")
        return LocalSourceProvider.revision

    def predicate_for_revision(self, revision):
        # TODO: Want to return None here ideally
        return VersionPredicate('"{}"'.format(revision))
