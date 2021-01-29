"""
Create shell applications using Click, with several out-of-the-box bells and whistles for a snazzier look and simple customization
"""

# Click Exports for easy access

from click.decorators import confirmation_option
from click.decorators import help_option
from click.decorators import make_pass_decorator
from click.decorators import option
from click.decorators import pass_context
from click.decorators import pass_obj
from click.decorators import password_option
from click.decorators import version_option

# Namespace Exports

from . import globals
from . import chars
from . import utils
from . import multicommand
from . import types
from . import cmd

# Class Exports

from ._cmd_factories import ClickCmdShell
from .shell import MultiCommandShell, Shell

# Decorator Exports

from .decorators import (
    shell, argument,
    prettyCommand as command,
    prettyGroup as group,
    repeatable, add_options
)


__version__ = '21.1.28.1'