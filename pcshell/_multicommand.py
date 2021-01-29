import types
from ._cmd_factories import ClickCmdShell

from .utils import HasKey


CUSTOM_COMMAND_PROPS = [
    'exit',
]

def CustomCommandPropsParser(shell: ClickCmdShell, cmd: object, name: str) -> None:
    if HasKey('exit', cmd):
        setattr(shell, 'do_%s' % name, types.MethodType(lambda self, arg: True, shell))