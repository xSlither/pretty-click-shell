from ._compat import get_method_type
from ._cmd_factories import ClickCmdShell

from .types import HasKey


CUSTOM_COMMAND_PROPS = [
    'exit',
]

def CustomCommandPropsParser(shell: ClickCmdShell, cmd: object, name: str) -> None:
    if HasKey('exit', cmd):
        setattr(shell, 'do_%s' % name, get_method_type(lambda self, arg: True, shell))