from __future__ import division, absolute_import, print_function

__all__ = ['config', 'provide_cli_options', '_config']

from pathlib2 import Path
import yaml
import os
import six

from .runner import *
from .xcode import *
from .platform import *
from .errors import *
from .defaults import *

# TODO: This all needs to be cleaned up and made more generic. More configs will be added over time and this will only get worse
# TODO: Allow config file to be relocated and specified on command line
# TODO: Allow subcommands to easily override configs

cli_options = dict()


def better_bool(value):
    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return bool(value)
    elif isinstance(value, str):
        value = value.strip()
        if value.lower() in ('1', 'true', 'yes'):
            return True
        elif value.lower() in ('0', 'false', 'no'):
            return False
    raise TypeError(value)


def make_config():
    config = Defaults()

    type_converters = dict(
        build_log_directory=Path,
        build_path=Path,
        checkouts_path=Path,
        CI=better_bool,
        DEBUG=better_bool,
        derived_data_path=Path,
        library_directory=Path,
        punic_path=Path,
        repo_cache_directory=Path,
        root_path=Path,
    )
    config.type_converters = type_converters

    providers = []

    registration_provider = dict(
        color=True,
        configuration=None,
        DEBUG=False,
        dry_run=False,
        echo=False,
        fetch=False,
        library_directory=Path('~/Library/Application Support/io.schwa.Punic').expanduser(),
        logs_path=Path('~/Library/Logs/Punic').expanduser(),
        platform=None,
        repo_overrides=dict(),
        root_path=Path.cwd(),
        skips=[],
        toolchain=None,
        use_ssh=False,
        use_submodules=False,
        verbose=False,
        xcode=Xcode.default(),
    )

    local_provider = {}
    if Path('punic.yaml').exists():
        local_provider = YAMLFileDefaultsProvider(Path('punic.yaml'), prefix_key='defaults')

    o = config.obj
    lambdas = dict(
        build_log_directory =    lambda _: o.logs_path / 'Build',
        build_path =             lambda _: o.punic_path / 'Build',
        cartfile_resolved_path = lambda _: o.root_path / 'Cartfile.resolved',
        checkouts_path =         lambda _: o.punic_path / 'Checkouts',
        continuous_integration = lambda _: 'CI' in config,
        derived_data_path =      lambda _: config.obj.library_directory / 'DerivedData',
        platforms =              lambda _: parse_platforms(config.obj.platform),
        punic_path =             lambda _: o.root_path / 'Carthage',
        repo_cache_directory =   lambda _: o.library_directory / 'repo_cache',
        runner_cache_path =      lambda _: o.library_directory / 'cache.shelf',
    )
    lambdas = LambdaDefaultsProvider(lambdas, o)

    config.providers = [
        ('synthetic', lambdas),
        ('registration', registration_provider),
        ('environ', EnvironDefaultsProvider()),
        ('cli', cli_options),
        ('local_provider', local_provider),
        ('memory_store', config.memory_store),
    ]

    return config


def provide_cli_options(**kwargs):
    xcode_version = kwargs.get('xcode_version', None)
    if xcode_version:
        kwargs['xcode'] = Xcode.with_version(kwargs['xcode_version'])
    if 'xcode_version' in kwargs:
        del kwargs['xcode_version']

    global cli_options
    cli_options.update(dict((key, value) for key, value in kwargs.items() if value is not None))


#        runner.cache_path = self.library_directory / "cache.shelf"

# def read(self, path):
#     # type: (Path) -> None
#
#     d = yaml.safe_load(path.open())
#     if not d:
#         return
#     if 'defaults' in d:
#         defaults = d['defaults']
#         if 'configuration' in defaults:
#             self.configuration = defaults['configuration']
#         if 'platforms' in defaults:
#             self.platforms = parse_platforms(defaults['platforms'])
#         elif 'platform' in defaults:
#             self.platforms = parse_platforms(defaults['platform'])
#         if 'xcode-version' in defaults:
#             self.xcode_version = six.text_type(defaults['xcode-version'])
#
#         if 'use-ssh' in defaults:
#             self.use_ssh = defaults['use-ssh']
#
#     if 'repo-overrides' in d:
#         self.repo_overrides = d['repo-overrides']
#
#     if 'skips' in d:
#         self.skips = d['skips'] or []

_config = make_config()
config = _config.obj
