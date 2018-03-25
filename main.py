"""Lambda function that executes pycodestyle, a static file linter."""

from lintipy import Handler

Handler('PEP8', 'pycodestyle', '.', )
