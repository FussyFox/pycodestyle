"""Lambda function that executes pycodestyle, a static file linter."""

from lintipy import Handler

handle = Handler('PEP8', 'pycodestyle', '.', )
