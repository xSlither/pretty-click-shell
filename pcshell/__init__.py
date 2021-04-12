"""
## pretty-click-shell

Author: Chase M. Allen

Description: Create shell applications using Click, with several out-of-the-box bells and whistles for a snazzier look and simple customization
"""

# Click Exports for easy access

from click.decorators import confirmation_option
from click.decorators import help_option
from click.decorators import make_pass_decorator
from click.decorators import pass_context
from click.decorators import pass_obj
from click.decorators import password_option
from click.decorators import version_option

from click.core import echo

from click.core import Context

# Namespace Exports

from . import globals
from . import _colors as colors
from . import chars
from . import utils
from . import multicommand
from . import types

# Class Exports

from ._cmd_factories import ClickCmdShell
from .shell import MultiCommandShell, Shell

try:
    from ._lexer import ShellLexer
    from ._completion import ClickCompleter, StyledFuzzyCompleter
except: pass

# Decorator Exports

from .decorators import (
    shell, argument, option,
    prettyCommand as command,
    prettyGroup as group,
    repeatable, add_options
)


__version__ = '0.1.2'