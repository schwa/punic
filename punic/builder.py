from __future__ import division, absolute_import, print_function

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
from .config import *

class Builder(object):

    def __init__(self, session):
        self.session = session

    def build(self, dependencies):
        # type: ([str]) -> None

        logging.info('Using xcode version: {}'.format(config.xcode))

        configuration, platforms = config.configuration, config.platforms

        if not config.build_path.exists():
            config.build_path.mkdir(parents=True)

        filtered_dependencies = self.session.ordered_dependencies(name_filter=dependencies)

        checkouts = [self.session.make_checkout(identifier=node.identifier, revision=node.version) for node in filtered_dependencies]

        skips = config.skips

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


    def _build_one(self, platform, project, scheme, configuration):

        if config.dry_run:
            for sdk in platform.sdks:
                logging.warn('<sub>DRY-RUN: (Not) Building</sub>: <ref>{}</ref> (scheme: {}, sdk: {}, configuration: {})...'.format(project.path.name, scheme, sdk, configuration))
            return

        all_products = []

        toolchain = config.toolchain

        # Build device & simulator (if sim exists)
        for sdk in platform.sdks:
            logging.info('<sub>Building</sub>: <ref>{}</ref> (scheme: {}, sdk: {}, configuration: {})...'.format(project.path.name, scheme, sdk, configuration))

            derived_data_path = config.derived_data_path

            resolved_configuration = configuration if configuration else project.default_configuration
            if not resolved_configuration:
                logging.warn("<err>Warning</err>: No configuration specified for project and no default configuration found. This could be a problem.")

            arguments = XcodeBuildArguments(scheme=scheme, configuration=resolved_configuration, sdk=sdk, toolchain=toolchain, derived_data_path=derived_data_path)

            try:
                all_products += project.build(arguments=arguments)
            except BuildFailure as e:

                logging.error('<err>Error</err>: Failed to build - result code <echo>{}</echo>'.format(e.returncode))
                logging.error('Command: <echo>{}</echo>'.format(e.cmd))

                project_name = config.root_path.name

                log_path = config.build_log_directory / "{}.log".format(project_name)
                logging.error('xcodebuild log written to <ref>{}</ref>'.format(log_path))
                log_path.open("w").write(e.output)

                # logging.error(e.output)
                exit(e.returncode)

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
            output_product.target_build_dir = config.build_path / platform.output_directory_name

            ########################################################################################################

            logging.debug('<sub>Copying binary</sub>...')
            if output_product.product_path.exists():
                shutil.rmtree(output_product.product_path)

            if not device_product.product_path.exists():
                raise PunicException("No product at: {}".format(device_product.product_path))

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

