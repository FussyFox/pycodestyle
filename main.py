"""Lambda function that executes pycodestyle, a static file linter."""
from lintipy import CheckRun


handle = CheckRun.as_handler('pycodestyle', 'pycodestyle', '.', )
