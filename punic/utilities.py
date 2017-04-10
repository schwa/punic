from __future__ import division, absolute_import, print_function

__all__ = ['work_directory', 'timeit', 'deprecated', 'unimplemented', 'shorten_path', 'ensure_directory_exists']

import os
import time
import punic
import subprocess
from pathlib2 import Path

from .errors import *

def deprecated():
    raise DeprecatedError()

def unimplemented():
    raise UnimplementedError()

@contextlib.contextmanager
def work_directory(path):
    # type: (Union[Path, None]) -> None
    saved_wd = None
    if path:
        path = str(path)
        saved_wd = os.getcwd()
        os.chdir(path)
    try:
        yield
    except:
        raise
    finally:
        if saved_wd:
            os.chdir(saved_wd)


@contextlib.contextmanager
def timeit(task=None, log=None):
    # type: (Union[str, None], Union[bool, None]) -> None
    if log is None:
        log = punic.current_session.config.log_timings
    start = time.time()
    yield
    end = time.time()
    if log:
        logging.info('Task \'<ref>{}</ref>\' took <echo>{:.6f}</echo> seconds.'.format(task if task else '<unnamed task>', end - start))


def reveal(path):
    #type: (Path) -> None
    subprocess.check_call(['open', str(path.parent)])

def shorten_path(path):

    path = path.expanduser()

    if str(path).startswith(str(Path.cwd())):
        return path.relative_to(Path.cwd())

    if str(path).startswith(str(Path.home())):
        return Path('~') / path.relative_to(Path.home())

    return path


def ensure_directory_exists(path):
    if path.exists() == False:
        path.mkdir(parents=True)
    if not path.is_dir():
        raise PunicException('No such directory at {}'.format(path))
