
from pathlib2 import Path

from punic.utilities import work_directory
from punic.runner import *

import tempfile
import os

quick_tests_only = bool(int(os.environ.get('QUICK_TEST_ONLY', '0')))

def test_main():
    temp_dir = Path(tempfile.mkdtemp())

    with work_directory(temp_dir):
        output = runner.check_run('punic')

def test_clean():
    temp_dir = Path(tempfile.mkdtemp())

    if quick_tests_only:
        return

    with work_directory(temp_dir):
        output = runner.check_run('punic clean --all')



def test_search():
    temp_dir = Path(tempfile.mkdtemp())
    if quick_tests_only:
        return

    with work_directory(temp_dir):
        output = runner.check_run('punic search SwiftIO')

def test_version():
    temp_dir = Path(tempfile.mkdtemp())

    with work_directory(temp_dir):
        output = runner.check_run('punic --verbose version')
