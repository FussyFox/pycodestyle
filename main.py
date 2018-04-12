"""Lambda function that executes pycodestyle, a static file linter."""
import logging
import sys

from lintipy import Handler

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(logging.StreamHandler(sys.stdout))


def handle(*args, **kwargs):
    Handler('PEP8', 'pycodestyle', '.', )(*args, **kwargs)
