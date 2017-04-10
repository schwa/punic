from __future__ import division, absolute_import, print_function

__all__ = ['punic_cli', 'main']

import logging.handlers
import sys
import click
from click_didyoumean import DYMGroup
from pathlib2 import Path
import yaml

import punic
import punic.shshutil as shutil

from .copy_frameworks import *
from .logger import *
from .semantic_version import *
from .utilities import *
from .version_check import *
from .config_init import *
from .carthage_cache import *
from punic import *
from .runner import *
from .checkout import *
from .search import *
from .styling import styled_print
from .graph import make_graph
from .xcode import Xcode
from .builder import Builder
from .config import *


@click.group(cls=DYMGroup)
@click.option('--echo', default=None, is_flag=True, help="""Echo all commands to terminal.""")
@click.option('--verbose', default=None, is_flag=True, help="""Verbose logging.""")
@click.option('--color/--no-color', default=None, is_flag=True, help="""TECHNICOLOR.""")
@click.option('--timing/--no-timing', default=None, is_flag=True, help="""Log timing info""")
@click.pass_context
def punic_cli(context, echo, verbose, timing, color):
    ### TODO: Clean this up!

    provide_cli_options(echo=echo, verbose=verbose, log_timings=timing, color=color)

    # Configure click
    context.token_normalize_func = lambda x: x if not x else x.lower()

    # Color:
    if color is None and config.continuous_integration:
        config.color = False

    configure_logging()

    runner.echo = echo

    # Set up punic
    session = Session()
    context.obj = session


def configure_logging():
    # Configure logging
    level = logging.DEBUG if config.verbose else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = HTMLFormatter()

    # create console handler and set level to debug
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(stream_handler)

    ensure_directory_exists(config.logs_path)
    log_path = config.logs_path / "punic.log"
    needs_rollover = log_path.exists()

    file_handler = logging.handlers.RotatingFileHandler(str(log_path), backupCount=4)
    if needs_rollover:
        file_handler.doRollover()
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(HTMLStripperFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")))
    logger.addHandler(file_handler)

    for name in ['boto', 'requests.packages.urllib3']:
        named_logger = logging.getLogger(name)
        named_logger.setLevel(logging.WARNING)
        named_logger.propagate = True

    formatter.color = config.color


@punic_cli.command()
@click.pass_context
@click.option('--use-submodules', default=None, help="""Add dependencies as Git submodules""")
@click.option('--use-ssh', default=None, help="""Use SSH for downloading GitHub repositories""")
def fetch(context, **kwargs):
    """Fetch the project's dependencies.."""
    logging.info("<cmd>fetch</cmd>")
    session = context.obj
    config.fetch = True  # obviously
    provide_cli_options(**kwargs)

    with timeit('fetch'):
        with error_handling():
            session.fetch()


@punic_cli.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--use-submodules', default=None, help="""Add dependencies as Git submodules""")
@click.option('--use-ssh', default=None, is_flag=True, help="""Use SSH for downloading GitHub repositories""")
@click.option('--export-diagnostics', default=False, is_flag=True, help="""Export a diagnostic file to help with bug reporting""")
def resolve(context, **kwargs):
    """Resolve dependencies and output `Carthage.resolved` file.

    This sub-command does not build dependencies. Use this sub-command when a dependency has changed and you just want to update `Cartfile.resolved`.
    """
    session = context.obj
    logging.info("<cmd>Resolve</cmd>")
    provide_cli_options(**kwargs)

    with timeit('resolve'):
        with error_handling():
            session.resolve(export_diagnostics = kwargs['export_diagnostics'])


@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
@click.option('--toolchain', default=None, help="""Xcode toolchain to use""")
@click.option('--dry-run', default=None, is_flag=True, help="""Do not actually perform final build""")
@click.option('--use-submodules', default=None, help="""Add dependencies as Git submodules""")
@click.option('--use-ssh', default=None, is_flag=True, help="""Use SSH for downloading GitHub repositories""")
@click.argument('deps', nargs=-1)
def build(context, **kwargs):
    """Fetch and build the project's dependencies."""
    logging.info("<cmd>Build</cmd>")
    session = context.obj
    provide_cli_options(**kwargs)

    deps = kwargs['deps']

    logging.debug('Platforms: {}'.format(config.platforms))
    logging.debug('Configuration: {}'.format(config.configuration))

    with timeit('build'):
        with error_handling():
            builder = Builder(session)
            builder.build(dependencies=deps)


@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
@click.option('--toolchain', default=None, help="""Xcode toolchain to use""")
@click.option('--use-submodules', default=None, help="""Add dependencies as Git submodules""")
@click.option('--use-ssh', default=None, is_flag=True, help="""Use SSH for downloading GitHub repositories""")
@click.argument('deps', nargs=-1)
def update(context, **kwargs):
    """Update and rebuild the project's dependencies."""
    logging.info("<cmd>Update</cmd>")
    session = context.obj
    provide_cli_options(**kwargs)

    deps = kwargs['deps']

    with timeit('update'):
        with error_handling():
            session.resolve()

            builder = Builder(session)
            builder.build(dependencies=deps)


@punic_cli.command()
@click.pass_context
@click.option('--derived-data', default=False, is_flag=True, help="""Clean the punic derived data directory.""")
@click.option('--caches', default=False, is_flag=True, help="""Clean the global punic files.""")
@click.option('--build', default=False, is_flag=True, help="""Clean the locate Carthage/Build directorys.""")
@click.option('--all', default=False, is_flag=True, help="""Clean all.""")
def clean(context, derived_data, caches, build, all):
    """Clean project & punic environment."""
    logging.info("<cmd>Clean</cmd>")
    punic = context.obj

    with timeit('clean'):
        if build or all:
            logging.info('Erasing build directory: <path>{}</path>'.format(shorten_path(config.build_path)))
            if config.build_path.exists():
                shutil.rmtree(config.build_path)

        if derived_data or all:
            logging.info('Erasing derived data directory: <path>{}</path>'.format(shorten_path(config.derived_data_path)))
            if config.derived_data_path.exists():
                shutil.rmtree(config.derived_data_path)

        if caches or all:
            if config.repo_cache_directory.exists():
                logging.info('Erasing repo cache directory: <path>{}</path>'.format(shorten_path(config.repo_cache_directory)))
                shutil.rmtree(config.repo_cache_directory)
            logging.info('Erasing run cache file: <path>{}</path>'.format(shorten_path(runner.cache_path)))
            runner.reset()


@punic_cli.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--use-submodules', default=None, help="""Add dependencies as Git submodules""")
@click.option('--use-ssh', default=None, is_flag=True, help="""Use SSH for downloading GitHub repositories""")
@click.option('--open', default=False, is_flag=True, help="""Open the graph image file.""")
def graph(context, fetch, use_submodules, use_ssh, open):
    """Output resolved dependency graph."""
    logging.info("<cmd>Graph</cmd>")
    session = context.obj
    config.fetch = fetch
    if use_submodules:
        config.use_submodules = use_submodules
    if use_ssh:
        config.use_ssh = use_ssh
    with timeit('graph'):
        make_graph(session, open)


@punic_cli.command(name='copy-frameworks')
@click.pass_context
def copy_frameworks(context):
    """In a Run Script build phase, copies each framework specified by a SCRIPT_INPUT_FILE environment variable into the built app bundle."""
    copy_frameworks_main()


# noinspection PyUnusedLocal
@punic_cli.command()
@click.pass_context
@click.option('--check/--no-check', default=True, help="""Check for latest version.""")
@click.option('--simple', is_flag=True, default=False, help="""Only display simple version info. Implies --no-check.""")
@click.option('--xcode', is_flag=True, default=False, help="""Display xcode versions.""")
def version(context, check, simple, xcode):
    """Display the current version of Punic."""

    session = context.obj

    if simple:
        print("{}".format(punic.__version__))
    else:
        styled_print('Punic version: <version>{}</version>'.format(punic.__version__))

        if config.verbose:
            styled_print('Punic path: <ref>{}</ref> '.format(punic.__file__))

        sys_version = sys.version_info
        sys_version = SemanticVersion.from_dict(dict(major=sys_version.major, minor=sys_version.minor, micro=sys_version.micro, releaselevel=sys_version.releaselevel, serial=sys_version.serial, ))
        styled_print('Python version: <version>{}</version>'.format(sys_version))
        if config.verbose:
            styled_print('Python path: <path>{}</path> '.format(sys.executable))

        if xcode or config.verbose:
            styled_print("Xcode(s):")
            for xcode in Xcode.find_all():
                s = '\t<path>{}</path>: <version>{}</version>'.format(xcode.path, xcode.version)
                if xcode.is_default:
                    s += ' (default)'
                    styled_print(s)

        if check:
            version_check(verbose=True, timeout=None, failure_is_an_option=False)


@punic_cli.command()
@click.pass_context
def readme(context):
    """Opens punic readme in your browser (https://github.com/schwa/punic/blob/HEAD/README.markdown)"""
    click.launch('https://github.com/schwa/punic/blob/HEAD/README.markdown')


@punic_cli.command()
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
@click.option('--toolchain', default=None, help="""Xcode toolchain to use""")
@click.option('--use-submodules', default=None, help="""Add dependencies as Git submodules""")
@click.option('--use-ssh', default=None, is_flag=True, help="""Use SSH for downloading GitHub repositories""")
@click.argument('deps', nargs=-1)
@click.pass_context
def list(context, **kwargs):
    """Lists all platforms, projects, xcode projects, schemes for all dependencies."""
    punic = context.obj
    provide_cli_options(**kwargs)
    deps = kwargs['deps']

    configuration, platforms = config.configuration, config.platforms

    if not config.build_path.exists():
        config.build_path.mkdir(parents=True)

    filtered_dependencies = punic.ordered_dependencies(name_filter=deps)

    checkouts = [punic.make_checkout(identifier=node.identifier, revision=node.version) for node in filtered_dependencies]

    tree = {}

    for platform in platforms:
        tree[platform.name] = {}
        for checkout in checkouts:
            tree[platform.name][str(checkout.identifier)] = {'projects':{}}
            checkout.prepare()
            for project in checkout.projects:
                tree[platform.name][str(checkout.identifier)]['projects'][project.path.name] = {'schemes':{}}
                tree[platform.name][str(checkout.identifier)]['projects'][project.path.name]['path'] = str(project.path.relative_to(config.checkouts_path))
                schemes = project.schemes
                schemes = [scheme for scheme in schemes if scheme.framework_targets]
                schemes = [scheme for scheme in schemes if platform.device_sdk in scheme.supported_platform_names]
                tree[platform.name][str(checkout.identifier)]['projects'][project.path.name]['schemes'] = [scheme.name for scheme in schemes]


    yaml.safe_dump(tree, stream = sys.stdout)

@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--xcode', default=None)
def init(context, **kwargs):
    """Generate punic configuration file."""
    config_init(**kwargs)


@punic_cli.group(cls=DYMGroup)
@click.pass_context
def cache(context):
    """Cache punic build artifacts to Amazon S3"""
    pass


@cache.command()
@click.pass_context
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
@click.option('--force', default=False, is_flag=True, help="""Force publishing""")
def publish(context, xcode_version, force):
    """Generates and uploads the cache archive for the current Cartfile.resolved"""
    with error_handling():
        logging.info("<cmd>Cache Publish</cmd>")
        punic = context.obj
        if xcode_version:
            config.xcode = Xcode.with_version(xcode_version)
        carthage_cache = CarthageCache(config=punic.config)
        logging.info("Cache filename: <ref>'{}'</ref>".format(carthage_cache.archive_name_for_project()))
        carthage_cache.publish(force = force)



@cache.command()
@click.pass_context
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
def install(context, xcode_version):
    """Installs the cache archive for the current Cartfile.resolved"""
    with error_handling():
        logging.info("<cmd>Cache Install</cmd>")
        punic = context.obj
        if xcode_version:
            config.xcode = Xcode.with_version(xcode_version)
        carthage_cache = CarthageCache(config=punic.config)
        logging.info("Cache filename: <ref>'{}'</ref>".format(carthage_cache.archive_name_for_project()))
        carthage_cache.install()



@punic_cli.command()
@click.pass_context
@click.argument('name')
@click.option('--append', is_flag=True, default=False, help="""Add a selected project to a Cartfile""")
@click.option('--language', default='swift', help="""Search for projects of specified language""")
def search(context, name, append, language):
    """Search github for repositories and optionally add them to a Cartfile."""
    punic = context.obj

    github_search(punic, name, cartfile_append=append, language=language)


def main():
    try:
        punic_cli()
    except SystemExit:
        if _config.get('DEBUG', False):
            _config.dump()
        raise

