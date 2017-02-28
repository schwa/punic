from __future__ import division, absolute_import, print_function

__all__ = ['Repository', 'Revision']

from flufl.enum import Enum
import functools
import hashlib
import affirm
import six
import logging

from memoize import mproperty
from pathlib2 import Path

# Ideally we could six.urllib but this causes problem with nosetests!
if six.PY2:
    import urlparse
elif six.PY3:
    import urllib.parse as urlparse

from .runner import *
from .config import *
from .errors import *
from .cartfile import *
from .semantic_version import *
from .errors import NoSuchRevision


class Repository(object):
    def __init__(self, punic, identifier, repo_path=None):
        self.punic = punic
        self.identifier = identifier
        if repo_path:
            self.path = repo_path
        else:
            remote_url = self.identifier.remote_url.encode("utf-8")
            url_hash = hashlib.md5(remote_url).hexdigest()
            self.path = punic.config.repo_cache_directory / "{}_{}".format(self.identifier.project_name, url_hash)

        self.specifications_cache = dict()

    def __repr__(self):
        return str(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    def check_work_directory(self):
        if not self.path.exists():
            raise RepositoryNotClonedError()

    # @property
    # def config(self):
    #     return self.punic.config

    @mproperty
    def tags(self):
        """Return a list of Tag objects representing git tags. Only tags that are valid semantic versions are returned"""
        # type: () -> [Tag]

        self.check_work_directory()

        output = runner.check_run('git tag', cwd=self.path)
        tags = [tag for tag in output.split('\n') if tag]

        if config.verbose:
            bad_tags = [tag for tag in tags if not SemanticVersion.is_semantic(tag)]
            if bad_tags:
                logging.warning("<err>Warning</err>: Found tags in \'{}\' that are not semantic: {}".format(self, ', '.join(['\'{}\''.format(tag) for tag in bad_tags])))

        tags = [Revision(repository=self, revision=tag, revision_type=Revision.Type.tag) for tag in tags if SemanticVersion.is_semantic(tag)]
        return sorted(tags)

    def rev_parse(self, s):
        # type: (str) -> str

        self.check_work_directory()

        result = runner.run('git rev-parse "{}"'.format(s), echo=False, cwd=self.path)
        if result.return_code == 0:
            return result.stdout.strip()

        # TODO: assumes remote is called origin.
        command = 'git rev-parse "origin/{}"'.format(s)
        result = runner.run(command, echo=False, cwd=self.path)
        if result.return_code == 0:
            return result.stdout.strip()
        raise Exception('{}: \'{}\' failed with {}'.format(self, command, result))

    def checkout(self, revision):
        # type: (Revision) -> None
        logging.debug('Checking out <ref>{}</ref> @ revision <rev>{}</rev>'.format(self, revision))
        self.check_work_directory()
        try:
            runner.check_run('git checkout "{}"'.format(revision.sha), cwd=self.path)
        except Exception:
            raise NoSuchRevision(repository=self, revision=revision)

        runner.check_run('git submodule update --init --recursive', cwd=self.path)


    def fetch(self):
        if not self.path.exists():
            logging.debug('<sub>Cloning</sub>: <ref>{}</ref>'.format(self))

            url = self.identifier.remote_url

            parsed_url = urlparse.urlparse(url)
            if parsed_url.scheme == 'file':
                repo = parsed_url.path
            else:
                repo = url

            runner.check_run('git clone --recursive --recurse-submodules "{}" "{}"'.format(repo, str(self.path)), cwd=self.path.parent)
        else:
            self.check_work_directory()

            logging.info('<sub>Fetching</sub>: <ref>{}</ref>'.format(self))
            runner.check_run('git fetch', cwd=self.path)


    def specifications_for_revision(self, revision):
        # type: (Revision) -> [Specification]

        assert not revision or isinstance(revision, Revision)

        # logger.debug('Getting cartfile from revision {} of {})'.format(revision, self))

        if revision in self.specifications_cache:
            return self.specifications_cache[revision]
        elif revision is None and self == self.punic.root_project:
            cartfile = Cartfile(use_ssh=self.config.use_ssh, overrides=config.repo_overrides)
            specifications = []

            cartfile_path = self.path / 'Cartfile'
            cartfile_private_path = self.path / 'Cartfile.private'

            if cartfile_path.exists():
                cartfile.read(cartfile_path)
                specifications += cartfile.specifications

            if cartfile_private_path.exists():
                cartfile.read(cartfile_private_path)
                if set(specifications).intersection(cartfile.specifications):
                    raise PunicRepresentableError(
                        "Specifications in your Cartfile.private conflict with specifications within your Cartfile.")
                specifications += cartfile.specifications

            if not specifications:
                raise PunicRepresentableError(
                    "No specifications found in {} or {}".format(cartfile_path.relative_to(Path.cwd()), cartfile_private_path.relative_to(Path.cwd())))

        else:
            self.check_work_directory()

            try:
                parsed_revision = self.rev_parse(revision)
            except:
                print("FAILED") # JIWTODO
                return []

            result = runner.run('git show "{}:Cartfile"'.format(parsed_revision), cwd=self.path)
            if result.return_code != 0:
                specifications = []
            else:
                data = result.stdout
                cartfile = Cartfile(use_ssh=self.config.use_ssh, overrides=config.repo_overrides)
                cartfile.read(data)
                specifications = cartfile.specifications

        self.specifications_cache[revision] = specifications
        return specifications

    def revisions_for_predicate(self, predicate):
        # type: (VersionPredicate) -> [Tag]
        return [tag for tag in self.tags if predicate.test(tag.semantic_version)]


########################################################################################################################

@functools.total_ordering
class Revision(object):
    always_use_is_ancestor = False

    class Type(Enum):
        tag = 'tag'
        commitish = 'commitish'

    def __init__(self, repository, revision, revision_type, check = True):
        assert isinstance(repository, Repository)
        assert isinstance(revision, six.string_types)
        #        assert isinstance(revision_type, Revision.Type) # TODO: This doesn't work.
        self.repository = repository
        self.revision = revision
        self.revision_type = revision_type
        self.semantic_version = (SemanticVersion.string(self.revision) if self.revision_type == Revision.Type.tag else None)

        if check and not self.exists:
            raise NoSuchRevision(repository=repository, revision=revision)

    @mproperty
    def exists(self):
        # TODO: dont use exceptions for logic
        try:
            self.repository.rev_parse(self.revision)
        except:
            return False
        return True


    @mproperty
    def sha(self):
        assert self.repository
        return self.repository.rev_parse(self.revision)

    def __repr__(self):
        return str(self.revision)

    def __eq__(self, other):
        try:
            if self.semantic_version and other.semantic_version and not Revision.always_use_is_ancestor:
                return self.semantic_version == other.semantic_version
            else:
                return (self.revision, self.revision_type) == (other.revision, other.revision_type)
        except:
            logging.error(self.repository)
            raise

    # see: https://bugs.python.org/issue25732
    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        if self.semantic_version and other.semantic_version and not Revision.always_use_is_ancestor:
            return self.semantic_version < other.semantic_version
        else:
            self.repository.check_work_directory()

            result = runner.run('git merge-base --is-ancestor "{}" "{}"'.format(other.sha, self.sha), cwd=self.repository.path)
            if result.return_code == 0:
                return False
            if result.return_code == 1:
                return True
            else:
                raise Exception('git merge-base returned {} {} {} {} {}'.format(result.return_code, result.stderr, self.repository, other.sha, self.sha))

    def __hash__(self):
        # TODO: Should include repo too?
        return hash((self.revision, self.revision_type))
