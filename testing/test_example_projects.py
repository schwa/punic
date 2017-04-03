
from pathlib2 import Path

from punic.utilities import work_directory
from punic.runner import *

import punic.shshutil as shutil

import tempfile
import os

quick_tests_only = bool(int(os.environ.get('QUICK_TEST_ONLY', '0')))

def test_update_and_build():
    if quick_tests_only:
        return

    source = Path(__file__).parent / 'Examples'
    destination = Path(tempfile.mkdtemp()) / 'Examples'

    shutil.copytree(source, destination)

    project_paths = [path for path in destination.iterdir() if path.is_dir()]

    for project_path in project_paths:

        with work_directory(project_path):

            output = runner.check_run('punic update')

            # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.framework').exists()
            # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.framework').exists()
            # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.dSYM').exists()
            # assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.dSYM').exists()
            #
            # output = runner.check_run('punic build')
            #
