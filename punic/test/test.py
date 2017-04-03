
from click.testing import CliRunner
from pathlib2 import Path

from punic.punic_cli import punic_cli
from punic.utilities import work_directory
from punic.runner import *

import punic.shshutil as shutil

import tempfile
import os

quick_tests_only = bool(int(os.environ.get('QUICK_TEST_ONLY', '0')))

def setup():
    test_data_path = Path(__file__).parent / 'Examples/SwiftIO'

    items = ['Cartfile', 'Cartfile.resolved', 'punic.yaml']

    temp_dir = Path(tempfile.mkdtemp())

    for item in items:
        shutil.copy(test_data_path / item, temp_dir)

    return temp_dir


def test_update_and_build():
    if quick_tests_only:
        return

    temp_dir = setup()

    with work_directory(temp_dir):
        runner = Runner()
        output = runner.check_run('punic update')

        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.framework').exists()
        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.framework').exists()
        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.dSYM').exists()
        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.dSYM').exists()

        output = runner.check_run('punic build')


def test_list():
    if quick_tests_only:
        return

    temp_dir = setup()

    with work_directory(temp_dir):
        runner = Runner()
        output = runner.check_run('punic list')


def test_clean():
    if quick_tests_only:
        return

    temp_dir = setup()

    with work_directory(temp_dir):
        runner = Runner()
        output = runner.check_run('punic clean')


def test_version():
    temp_dir = Path(tempfile.mkdtemp())

    with work_directory(temp_dir):
        output = runner.check_run('punic version')
