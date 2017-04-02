from __future__ import division, absolute_import, print_function

__all__ = ['Runner', 'runner', 'Result', 'CalledProcessError']

import subprocess
import shlex
import shelve
from subprocess import CalledProcessError
from memoize import mproperty
import six
import logging
import os

class Result(object):
    def __init__(self):
        self.return_code = None
        self.stdout = None
        self.stderr = None

class Runner(object):
    def __init__(self, cache_path=None, echo=False, echo_directories=True, extra_env=None):
        self.cache_path = cache_path
        self.echo = echo
        self.echo_directories = echo_directories
        self.extra_env = extra_env

    @mproperty
    def shelf(self):
        if not self.cache_path:
            return None
        # noinspection PyBroadException
        try:
            shelf = shelve.open(str(self.cache_path))
            return shelf
        except:
            if self.cache_path.exists():
                logging.info("Resetting cache and trying again...")
                self.cache_path.unlink()
                shelf = shelve.open(str(self.cache_path))
                return self
            else:
                raise
        return shelf

    def reset(self):
        if self.cache_path.exists():
            self.shelf.close()
            self.cache_path.unlink()
            # TODO: Reopen

    def result(self, command):
        result = self.run(command)
        return result.return_code

    @staticmethod
    def convert_args(args):
        if isinstance(args, list) or isinstance(args, tuple):
            return [str(arg) for arg in args]
        elif isinstance(args, six.string_types):
            return shlex.split(args)
        else:
            return [str(args)]

    def can_run(self, args):
        args = self.convert_args(args)
        result = self.run(['/usr/bin/env', 'which', args[0]], echo=False)
        return True if result.return_code == 0 else False

    def check_run(self, *args, **kwargs):
        kwargs['check'] = True
        result = self.run(*args, **kwargs)
        return six.text_type(result.stdout)

    # TODO: Cleanup
    check_call = check_run

    def run(self, command, cwd=None, echo=None, cache_key=None, check=False, env=None, use_os_environ=True):
        args = self.convert_args(command)

        if echo or echo is None and self.echo:
            if cwd and self.echo_directories:
                logging.info('cd {}'.format(cwd))

            # TODO: Wont properly reproduce command if command is a string
            logging.info(' '.join(arg.replace(' ', '\\ ') for arg in args))

        if cache_key:
            # assert not env # TODO
            key = '{}{}'.format(cache_key, ' '.join(command))
            if key in self.shelf:
                # logger.debug('CACHE HIT: {}'.format(key))
                return_code, stdout, stderr = self.shelf[key]
                result = Result()
                result.return_code = return_code
                result.stdout = stdout
                result.stderr = stderr
                return result
            else:
                # logger.debug('CACHE MISS: {}'.format(key))
                pass

        stdout = subprocess.PIPE
        stderr = subprocess.PIPE if not check else subprocess.STDOUT

        if cwd:
            cwd = str(cwd)

        resolved_env = dict()
        if use_os_environ:
            resolved_env.update(os.environ)
        if env:
            resolved_env.update(env)
        if self.extra_env:
            resolved_env.update(self.extra_env)

        popen = subprocess.Popen(args, cwd=cwd, stdout=stdout, stderr=stderr, env=resolved_env)
        stdout, stderr = popen.communicate()

        if stdout is not None:
            stdout = stdout.decode('utf-8')
        if stderr is not None:
            stderr = stderr.decode('utf-8')

        return_code = popen.returncode

        if check and return_code != 0:
            # TODO
            if stdout:
                logging.debug(stdout)
            if stderr:
                logging.debug(stdout)
            raise CalledProcessError(return_code, command, stdout)

        if cache_key:
            key = '{}{}'.format(cache_key, ' '.join(command))
            self.shelf[key] = return_code, stdout, stderr

        result = Result()
        result.return_code = return_code
        result.stdout = stdout
        result.stderr = stderr

        return result


runner = Runner()
