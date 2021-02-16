"""Global variables used internally within pretty-click-shell
"""

# #####################################
HISTORY_FILENAME = '.pcshell-history'


MASTERSHELL_COMMAND_ALIAS_RESTART = ['restart']

BASIC_COMMAND_ALIAS_HELP = ['help', 'h', '--help']
BASIC_COMMAND_ALIAS_CLEARHISTORY = ['clearhistory', 'clshst', 'hstclear', 'hstcls', 'clearhst']

SHELL_COMMAND_ALIAS_CLEAR = ['cls', 'clear']
SHELL_COMMAND_ALIAS_QUIT = ['q', 'quit']
SHELL_COMMAND_ALIAS_EXIT = ['exit']
SHELL_COMMAND_ALIAS_REPEAT = ['repeat']
# #####################################


# ----------------------------------------------------
__IsShell__ = None

__LAST_COMMAND__ = None
__LAST_COMMAND_VISIBLE__ = None
__IS_REPEAT__ = False
__IS_REPEAT_EOF__ = False
__PREV_STDIN__ = None

__SHELL_PATH__ = []
__MASTER_SHELL__ = None

__CURRENT_LINE__ = ''
# ----------------------------------------------------