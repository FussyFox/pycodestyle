"""Lambda function that executes pycodestyle, a static file linter."""
import logging
import sys

from lintipy import Handler

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(logging.StreamHandler(sys.stdout))

handle = Handler('PEP8', 'pycodestyle', '.', )
