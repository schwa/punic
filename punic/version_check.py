from __future__ import division, absolute_import, print_function

__all__ = ['version_check']

import requests
import punic
import logging

from .semantic_version import *


def version_check(verbose=False, timeout=0.3, failure_is_an_option=True):
    try:
        log = logging.info if verbose else logging.debug

        log('<sub>Checking punic version...</sub>')

        current_version = SemanticVersion.string(punic.__version__)
        response = requests.get('https://pypi.python.org/pypi/punic/json', timeout=timeout)
        version_string = response.json()["info"]["version"]
        latest_version = SemanticVersion.string(version_string.strip())

        log('Current version: <rev>{}</rev>, latest version: <rev>{}</rev>'.format(current_version, latest_version))
        if current_version < latest_version:
            logging.warning("""You are using version <rev>{}</rev>, version <rev>{}</rev> is available.
            Use <echo>`pip install -U punic`</echo> to update to latest version.""".format(current_version, latest_version))
    # TODO: Duplicated code
    except requests.exceptions.ReadTimeout as e:
        logging.debug('<error>Failed to check versions')
        if not failure_is_an_option:
            raise e
    except requests.exceptions.ConnectTimeout as e:
        logging.debug('<error>Failed to check versions')
        if not failure_is_an_option:
            raise e
