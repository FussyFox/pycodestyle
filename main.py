"""Lambda function that executes pycodestyle, a static file linter."""
import logging
import sys

from lintipy import CheckRun

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(logging.StreamHandler(sys.stdout))


def handle(*args, **kwargs):
    """Handle that will be called by AWS lambda."""
    CheckRun('pycodestyle', 'pycodestyle', '.', )(*args, **kwargs)
