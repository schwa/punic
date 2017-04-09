
from pathlib2 import Path

from punic.utilities import work_directory
from punic.runner import *

import punic.shshutil as shutil

import tempfile
import os

quick_tests_only = bool(int(os.environ.get('QUICK_TEST_ONLY', '0')))

def build(source):


    destination = Path(tempfile.mkdtemp()) / source.name

    shutil.copytree(source, destination)

    with work_directory(destination):

        output = runner.check_run('punic resolve')
        output = runner.check_run('punic update')
        output = runner.check_run('punic fetch')
        output = runner.check_run('punic build')

        # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.framework').exists()
        # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.framework').exists()
        # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.dSYM').exists()
        # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.dSYM').exists()
        #
        # output = runner.check_run('punic build')
        #

examples_directory = Path(__file__).parent / 'Examples'

def test_local_1():
    build(examples_directory / 'local_1')

def test_rx():
    build(examples_directory / 'rx')

