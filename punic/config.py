from __future__ import division, absolute_import, print_function

__all__ = ['Config', 'config']

from pathlib2 import Path
import yaml
import logging
import os
import six

from .runner import *
from .xcode import *
from .platform import *


# TODO: This all needs to be cleaned up and made more generic. More configs will be added over time and this will only get worse
# TODO: Allow config file to be relocated and specified on command line
# TODO: Allow subcommands to easily override configs

class Config(object):
    def __init__(self):
        self.xcode = None
        self.repo_overrides = dict()

        self.root_path = Path.cwd()  # type: Path

        self.library_directory = Path('~/Library/Application Support/io.schwa.Punic').expanduser()
        if not self.library_directory.exists():
            self.library_directory.mkdir(parents=True)
        self.repo_cache_directory = self.library_directory / 'repo_cache'
        if not self.repo_cache_directory.exists():
            self.repo_cache_directory.mkdir(parents=True)
        self.punic_path = self.root_path / 'Carthage'
        self.build_path = self.punic_path / 'Build'
        self.checkouts_path = self.punic_path / 'Checkouts'

        self.derived_data_path = self.library_directory / "DerivedData"

        self.platforms = Platform.all
        self.configuration = None

        self.fetch = False
        self.xcode = Xcode.default()

        self.toolchain = None
        self.dry_run = False
        self.use_submodules = False
        self.use_ssh = False

        self.skips = []

        self.verbose = False
        self.echo = False

        self.continuous_integration = 'CI' in os.environ
        if self.continuous_integration:
            logging.info("Running on continuous integration")

        # Read in defaults from punic.yaml (or punic.yml if that exists)
        punic_configuration_path = Path('punic.yaml')
        if not punic_configuration_path.exists():
            punic_configuration_path = Path('punic.yml')
        if punic_configuration_path.exists():
            self.read(punic_configuration_path)
        runner.cache_path = self.library_directory / "cache.shelf"

    def update(self, **kwargs):
        for key, value in sorted(kwargs.items()):
            if value:
                if hasattr(self, key):
                    setattr(self, key, value)

        # Special case for platforms
        platform = kwargs['platform'] if 'platform' in kwargs else None
        if platform:
            self.platforms = parse_platforms(platform)

        if self.verbose and os.environ.get('DUMP_CONFIG', False):
            self.dump()

    def dump(self):

        logging.info('# Environment ##' + '#' * 64)

        logging.info('CWD: {}'.format(os.getcwd()))

        key_width = max([len(k) for k in os.environ.keys()] + [len(k) for k in self.__dict__.items()])

        os.environ.keys()

        for key, value in sorted(os.environ.items()):
            logging.info('{:{key_width}}: {}'.format(key, value, key_width = key_width + 1))

        logging.info('# Configuration ' + '#' * 64)

        for key, value in sorted(self.__dict__.items()):
            logging.info('{:{key_width}}: {}'.format(key, value, key_width = key_width + 1))
        logging.info('#' * 80)

    @property
    def xcode_version(self):
        return self.xcode.version if self.xcode else None

    @xcode_version.setter
    def xcode_version(self, value):
        xcode = Xcode.with_version(value)
        if value and not xcode:
            raise Exception('Could not find xcode version: {}'.format(value))
        if not xcode:
            xcode = Xcode.default()
        self.xcode = xcode

    def read(self, path):
        # type: (Path)

        d = yaml.safe_load(path.open())
        if not d:
            return
        if 'defaults' in d:
            defaults = d['defaults']
            if 'configuration' in defaults:
                self.configuration = defaults['configuration']
            if 'platforms' in defaults:
                self.platforms = parse_platforms(defaults['platforms'])
            elif 'platform' in defaults:
                self.platforms = parse_platforms(defaults['platform'])
            if 'xcode-version' in defaults:
                self.xcode_version = six.text_type(defaults['xcode-version'])

            if 'use-ssh' in defaults:
                self.use_ssh = defaults['use-ssh']

        if 'repo-overrides' in d:
            self.repo_overrides = d['repo-overrides']

        if 'skips' in d:
            self.skips = d['skips'] or []

config = Config()
