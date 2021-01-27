"""
Create shell applications using Click, with several out-of-the-box bells and whistles for a snazzier look and simple customization
"""

from . import globals as globals
from . import chars as chars

from .utils import (
    HasKey, ExtractPasswordAndSetEnv, 
    replacenth, suggest
)

from .types import (
    Tuple_IntString, 
    HiddenPassword
)

from .prog import (
    ProgressBar, ProgressBarCollection, 
    progressbar_collection
)

from .multicommand import (
    CUSTOM_COMMAND_PROPS, 
    CustomCommandPropsParser
)

from ._cmd_factories import ClickCmdShell
from .shell import MultiCommandShell, Shell

from .decorators import (
    shell, argument, 
    repeatable, add_options
)


__version__ = '21.1.27.1'