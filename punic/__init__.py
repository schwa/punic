from __future__ import division, absolute_import, print_function

__version__ = '0.2.8'
__all__ = ['Punic', 'current_session']

import os
from copy import copy
from pathlib2 import Path
import logging
from collections import defaultdict

from .cartfile import Cartfile
from .checkout import Checkout
from .config import config
from .repository import Repository, Revision
from .resolver import Resolver, Node
from .runner import runner
from .specification import ProjectIdentifier, Specification, VersionPredicate, VersionOperator
from .xcode import XcodeBuildArguments
import punic.shshutil as shutil
from .errors import NoSuchRevision
from .source_provider import *

current_session = None


class Punic(object):
    __slots__ = ['root_path', 'config', 'all_source_providers', 'root_project']

    def __init__(self, root_path=None):

        global current_session

        if not current_session:
            current_session = self

        self.config = config

        if root_path:
            self.config.root_path = root_path

        root_project_identifier = ProjectIdentifier(overrides=None, source="root", link=self.config.root_path, project_name=self.config.root_path.name)

        self.root_project = Repository(identifier=root_project_identifier, repo_path=self.config.root_path,
                                       is_root_project=True)

        self.all_source_providers = {root_project_identifier: self.root_project, }

    def _resolver(self, export_diagnostics = False):
        return Resolver(punic = self, root=Node(self.root_project.identifier, None), dependencies_for_node=self._dependencies_for_node, export_diagnostics = export_diagnostics)

    def _dependencies_for_node(self, node):
        assert not node.version or isinstance(node.version, Revision)
        dependencies = self.dependencies_for_project_and_tag(identifier=node.identifier, tag=node.version)
        return dependencies

    def resolve(self, export_diagnostics = False):
        # type: (bool) -> None
        resolver = self._resolver(export_diagnostics = export_diagnostics)
        build_order = resolver.resolve_build_order()

        for index, node in enumerate(build_order[:-1]):
            dependency, version = node.identifier, node.version
            logging.debug('{} <ref>{}</ref> <rev>{}</rev> <ref>{}</ref>'.format(index + 1, dependency, version.revision if version else '', dependency.link))

        specifications = [Specification(identifier=node.identifier, predicate=VersionPredicate('"{}"'.format(node.version.revision))) for node in build_order[:-1]]
        logging.debug("<sub>Saving</sub> <ref>Cartfile.resolved</ref>")

        cartfile = Cartfile(use_ssh=self.config.use_ssh, specifications=specifications)
        cartfile.write((self.config.root_path / 'Cartfile.resolved').open('w'))

    def graph(self):
        # type: (bool) -> DiGraph
        return self._resolver().resolve()

    # TODO: This can be deprecated and the fetch flag relied on instead
    def fetch(self, dependencies=None):
        configuration, platforms = self.config.configuration, self.config.platforms
        if not self.config.build_path.exists():
            self.config.build_path.mkdir(parents=True)
        filtered_dependencies = self._ordered_dependencies(name_filter=dependencies)
        checkouts = [self.make_checkout(identifier=dependency.identifier, revision=dependency.version) for dependency in filtered_dependencies]
        for checkout in checkouts:
            checkout.prepare()


    def make_checkout(self, identifier, revision):
        has_dependencies = len(self.dependencies_for_project_and_tag(identifier, revision)) > 0
        return Checkout(punic=self, identifier=identifier, revision=revision, has_dependencies=has_dependencies)


    def build(self, dependencies):
        # type: ([str]) -> None

        logging.info('Using xcode version: {}'.format(self.config.xcode))

        configuration, platforms = self.config.configuration, self.config.platforms

        if not self.config.build_path.exists():
            self.config.build_path.mkdir(parents=True)

        filtered_dependencies = self._ordered_dependencies(name_filter=dependencies)

        checkouts = [self.make_checkout(identifier=node.identifier, revision=node.version) for node in filtered_dependencies]

        skips = self.config.skips

        def filter_dependency(platform, checkout, project, scheme):
            platform = platform.name
            checkout = checkout.identifier.project_name
            project = project.path.name
            scheme = scheme.name

            for skip in skips:
                current = [ platform, checkout, project, scheme ][:len(skip)]
                if skip == current:
                    # print(skip)
                    # print(current)
                    # print('SKIP?')
                    return False
            return True

        for platform in platforms:
            for checkout in checkouts:
                checkout.prepare()
                for project in checkout.projects:
                    schemes = project.schemes

                    schemes = [scheme for scheme in schemes if scheme.framework_targets]
                    schemes = [scheme for scheme in schemes if platform.device_sdk in scheme.supported_platform_names]
                    for scheme in schemes:
                        if not filter_dependency(platform, checkout, project, scheme):
                            logging.warn('<err>Warning:</err> <sub>Skipping</sub>: {} / {} / {} / {}'.format(platform, checkout.identifier.project_name, project.path.name, scheme.name))
                            continue
                        self._build_one(platform, project, scheme.name, configuration)

    def _ordered_dependencies(self, name_filter=None):
        # type: (bool, [str]) -> [(ProjectIdentifier, Revision)]

        cartfile = Cartfile(use_ssh=self.config.use_ssh, overrides=config.repo_overrides)
        cartfile.read(self.config.root_path / 'Cartfile.resolved')

        def _predicate_to_revision(spec):
            source_provider = self._source_provider_for_identifier(spec.identifier)
            repository = source_provider._repository
            if spec.predicate.operator == VersionOperator.commitish:
                try:
                    return Revision(repository=repository, revision=spec.predicate.value, revision_type=Revision.Type.commitish, check = True)
                except NoSuchRevision as e:
                    logging.warning(e.message)
                    return None
                except:
                    raise
            else:
                raise GenericPunicException("Cannot convert spec to revision: {}".format(spec))


        dependencies = [(spec.identifier, _predicate_to_revision(spec)) for spec in cartfile.specifications]
        resolved_dependencies = self._resolver().resolve_versions(dependencies)
        resolved_dependencies = [dependency for dependency in resolved_dependencies if dependency.identifier.matches(name_filter)]
        return resolved_dependencies

    def _source_provider_for_identifier(self, identifier):
        # type: (ProjectIdentifier) -> SourceProvider
        if identifier in self.all_source_providers:
            return self.all_source_providers[identifier]
        else:
            source_provider = SourceProvider.source_provider_with_identifier(identifier=identifier)
            if self.config.fetch:
                source_provider.fetch()
            self.all_source_providers[identifier] = source_provider
            return source_provider

    def dependencies_for_project_and_tag(self, identifier, tag):
        # type: (ProjectIdentifier, Revision) -> [ProjectIdentifier, [Revision]]

        assert isinstance(identifier, ProjectIdentifier)
        assert not tag or isinstance(tag, Revision)

        source_provider = self._source_provider_for_identifier(identifier)
        specifications = source_provider.specifications_for_revision(tag)

        def make(specification):
            source_provider = self._source_provider_for_identifier(specification.identifier)
            tags = source_provider.revisions_for_predicate(specification.predicate)
            if specification.predicate.operator == VersionOperator.commitish:
                try:
                    revision = Revision(repository=source_provider._repository, revision=specification.predicate.value, revision_type=Revision.Type.commitish, check = True)
                except NoSuchRevision as e:
                    logging.warning("<err>Warning</err>: {}".format(e.message))
                    return None
                tags.append(revision)
                tags.sort()
            assert len(tags)
            return source_provider.identifier, tags

        dependencies = [make(specification) for specification in specifications]
        dependencies = [dependency for dependency in dependencies if dependency]
        return dependencies

    def _build_one(self, platform, project, scheme, configuration):

        if self.config.dry_run:
            for sdk in platform.sdks:
                logging.warn('<sub>DRY-RUN: (Not) Building</sub>: <ref>{}</ref> (scheme: {}, sdk: {}, configuration: {})...'.format(project.path.name, scheme, sdk, configuration))
            return

        all_products = []

        toolchain = self.config.toolchain

        # Build device & simulator (if sim exists)
        for sdk in platform.sdks:
            logging.info('<sub>Building</sub>: <ref>{}</ref> (scheme: {}, sdk: {}, configuration: {})...'.format(project.path.name, scheme, sdk, configuration))

            derived_data_path = self.config.derived_data_path

            resolved_configuration = configuration if configuration else project.default_configuration
            if not resolved_configuration:
                logging.warn("<err>Warning</err>: No configuration specified for project and no default configuration found. This could be a problem.")

            arguments = XcodeBuildArguments(scheme=scheme, configuration=resolved_configuration, sdk=sdk, toolchain=toolchain, derived_data_path=derived_data_path)

            all_products += project.build(arguments=arguments)

        self._post_process(platform, all_products)

    def _post_process(self, platform, products):
        # type: (punic.platform.Platform, List) -> None

        ########################################################################################################

        logging.debug("<sub>Post processing</sub>...")

        # TODO: QUESTION: Is it possible that this could mix targets with different SDKs?
        products_by_name_then_sdk = defaultdict(dict)
        for product in products:
            products_by_name_then_sdk[product.full_product_name][product.sdk] = product


        for products_by_sdk in products_by_name_then_sdk.values():

            products = products_by_sdk.values()

            # TODO: By convention sdk[0] is always the device sdk (e.g. 'iphoneos' and not 'iphonesimulator')
            primary_sdk = platform.sdks[0]

            device_product = products_by_sdk[primary_sdk]

            ########################################################################################################

            output_product = copy(device_product)
            output_product.target_build_dir = self.config.build_path / platform.output_directory_name

            ########################################################################################################

            logging.debug('<sub>Copying binary</sub>...')
            if output_product.product_path.exists():
                shutil.rmtree(output_product.product_path)

            if not device_product.product_path.exists():
                raise GenericPunicException("No product at: {}".format(device_product.product_path))

            shutil.copytree(device_product.product_path, output_product.product_path, symlinks=True)

            ########################################################################################################

            if len(products) > 1:
                logging.debug('<sub>Lipo-ing</sub>...')
                executable_paths = [product.executable_path for product in products]
                command = ['/usr/bin/xcrun', 'lipo', '-create'] + executable_paths + ['-output', output_product.executable_path]
                runner.check_run(command)
                mtime = executable_paths[0].stat().st_mtime
                os.utime(str(output_product.executable_path), (mtime, mtime))

            ########################################################################################################

            logging.debug('<sub>Copying swiftmodule files</sub>...')
            for product in products:
                for path in product.module_paths:
                    relative_path = path.relative_to(product.product_path)
                    shutil.copyfile(path, output_product.product_path / relative_path)

            ########################################################################################################

            logging.debug('<sub>Copying bcsymbolmap files</sub>...')
            for product in products:
                for path in product.bcsymbolmap_paths:
                    shutil.copy(path, output_product.target_build_dir)

            ########################################################################################################

            logging.debug('<sub>Producing dSYM files</sub>...')
            command = ['/usr/bin/xcrun', 'dsymutil', str(output_product.executable_path), '-o', str(output_product.target_build_dir / (output_product.executable_name + '.dSYM'))]
            runner.check_run(command)

            ########################################################################################################