
from pathlib2 import Path

from punic.utilities import work_directory
from punic.runner import *

import punic.shshutil as shutil

import tempfile
import os
import contextlib

quick_tests_only = bool(int(os.environ.get('QUICK_TEST_ONLY', '0')))

@contextlib.contextmanager
def example_work_directory(name):
    examples_directory = Path(__file__).parent / 'Examples'

    example_path = examples_directory / name

    work_path = Path(tempfile.mkdtemp()) / name
    print(work_path)

    shutil.copytree(example_path, work_path)

    with work_directory(work_path):
        yield

def test_local_1():
    with example_work_directory('local_1'):

        assert(Path('Cartfile.resolved').exists() == False)
        output = runner.check_run('punic resolve')
        assert(Path('Cartfile.resolved').open().read() == 'local "A" "."\n')

        # TODO: This should NOT be created by a resolve.
        # assert(Path('Carthage/Checkouts').exists() == False)
        output = runner.check_run('punic fetch')
        assert(Path('Carthage/Checkouts').is_dir() == True)

        # TODO: This should NOT be created by a fetch.
        # assert(Path('Carthage/Build').exists() == False)
        output = runner.check_run('punic build')
        assert(Path('Carthage/Build/Mac/A.framework').exists() == True)
        assert(Path('Carthage/Build/Mac/A.dSYM').exists() == True)

def test_rx():
    with example_work_directory('rx'):
        output = runner.check_run('punic update')
        assert(Path('Carthage/Build/Mac/RxBlocking.framework').exists() == True)
        assert(Path('Carthage/Build/Mac/RxBlocking.dSYM').exists() == True)
        assert(Path('Carthage/Build/Mac/RxCocoa.framework').exists() == True)
        assert(Path('Carthage/Build/Mac/RxCocoa.dSYM').exists() == True)
        assert(Path('Carthage/Build/Mac/RxSwift.framework').exists() == True)
        assert(Path('Carthage/Build/Mac/RxSwift.dSYM').exists() == True)
        assert(Path('Carthage/Build/Mac/RxTest.framework').exists() == True)
        assert(Path('Carthage/Build/Mac/RxTest.dSYM').exists() == True)


