"""Global variables used internally within pretty-click-shell
"""

HISTORY_FILENAME = '.pcshell-history'

__IsShell__ = None

__LAST_COMMAND__ = None
__LAST_COMMAND_VISIBLE__ = None
__IS_REPEAT__ = False
__IS_REPEAT_EOF__ = False
__PREV_STDIN__ = None

__SHELL_PATH__ = []
__MASTER_SHELL__ = None

__CURRENT_LINE__ = ''