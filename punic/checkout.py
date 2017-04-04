import itertools

import os
import re

from .config import config
from .errors import *
from .xcode import XcodeProject


class Checkout(object):

    def __init__(self, session, identifier, revision, has_dependencies):
        self.session = session
        self.identifier = identifier
        self.source_provider = session._source_provider_for_identifier(self.identifier)
        self.revision = revision
        self.checkout_path = config.checkouts_path / self.identifier.project_name

        self.has_dependencies = has_dependencies

    def prepare(self):

        self.source_provider.checkout(self.revision)

        if not self.checkout_path.exists():
            raise PunicException('No checkout at path: {}'.format(self.checkout_path))

        # We only need to bother making a symlink to <root>/Carthage/Build if dependency also has dependencies.
        if self.has_dependencies:
            # Make a Carthage/Build symlink inside checked out project.
            carthage_path = self.checkout_path / 'Carthage'
            if not carthage_path.exists():
                carthage_path.mkdir()

            carthage_symlink_path = carthage_path / 'Build'
            if carthage_symlink_path.exists():
                carthage_symlink_path.unlink()
            logging.debug('<sub>Creating symlink: <ref>{}</ref> to <ref>{}</ref></sub>'.format(carthage_symlink_path.relative_to(config.root_path), config.build_path.relative_to(config.root_path)))
            assert config.build_path.exists()

            # TODO: Generate this programatically.
            os.symlink("../../../Build", str(carthage_symlink_path))


    @property
    def projects(self):
        def _make_cache_identifier(project_path):
            rev = self.source_provider.canonical_name_for_revision(self.revision)
            cache_identifier = '{},{}'.format(rev, project_path.relative_to(self.checkout_path))
            return cache_identifier

        def test(path):
            relative_path = path.relative_to(self.checkout_path)
            if 'Carthage/Checkouts' in str(relative_path):
                return False
            return True

        project_paths = itertools.chain(self.checkout_path.glob("**/*.xcworkspace"), self.checkout_path.glob("**/*.xcodeproj"))
        project_paths = [path for path in project_paths if test(path)]
        if not project_paths:
            logging.warning("No projects/workspaces found in {}".format(self.checkout_path))
            return []

        projects = []
        schemes = []
        embedded_project_pattern = re.compile(r"\.(playground|xcodeproj)/[^/]+\.xcworkspace$")

        for project_path in project_paths:
            if embedded_project_pattern .search(str(project_path)):
                #print('Skipping project\'s embedded workspace:', project_path)
                continue
            project = XcodeProject(self, config.xcode, project_path, _make_cache_identifier(project_path))
            for scheme in list(project.scheme_names):
                if scheme in schemes:
                    project.info[2].remove(scheme)
                else:
                    schemes.append(scheme)
            if len(project.scheme_names) > 0:
                projects.append(project)
        return projects
