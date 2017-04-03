
from pathlib2 import Path

from punic.utilities import work_directory
from punic.runner import *

import tempfile


def test_version():
    temp_dir = Path(tempfile.mkdtemp())

    with work_directory(temp_dir):
        output = runner.check_run('punic version')
