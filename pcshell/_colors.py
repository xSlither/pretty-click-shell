"""Customizable colors used in the Shell
"""

from colorama import Fore, Back, Style


# Help Command Colors

HELP_USAGE_STYLE = Style.BRIGHT
HELP_USAGE_FORE = Fore.GREEN

HELP_TEXT_FORE = Style.DIM

HELP_OPTION_DESCRIPTION_STYLE = Style.DIM
HELP_OPTION_NAME_STYLE = Fore.YELLOW
HELP_OPTION_HEADER_FORE = Fore.WHITE
HELP_OPTION_HEADER_BACK = Back.MAGENTA
HELP_OPTION_HEADER_STYLE = Style.BRIGHT

HELP_ARGUMENT_DESCRIPTION_STYLE = Style.DIM
HELP_ARGUMENT_NAME_STYLE = Fore.YELLOW + Style.BRIGHT
HELP_ARGUMENT_CLASS_STYLE = Fore.CYAN
HELP_ARGUMENT_ARROW_STYLE = Fore.RED + Style.BRIGHT
HELP_ARGUMENT_HEADER_FORE = Fore.BLUE + Style.DIM
HELP_ARGUMENT_HEADER_BACK = Back.YELLOW
HELP_ARGUMENT_HEADER_STYLE = Style.BRIGHT

HELP_COMMAND_DESCRIPTION_STYLE = Style.DIM
HELP_COMMAND_NAME_STYLE = Fore.YELLOW
HELP_COMMAND_HEADER_FORE = Fore.WHITE
HELP_COMMAND_HEADER_BACK = Back.BLUE
HELP_COMMAND_HEADER_STYLE = Style.BRIGHT


# Exception Colors

USAGE_ERROR_STYLE = Fore.RED + Style.BRIGHT

CLICK_ERROR_STYLE = Fore.RED + Style.BRIGHT

UNEXPECTED_ERROR_TEXT_STYLE = Fore.YELLOW

PYTHON_ERROR_HEADER_FORE = Fore.WHITE
PYTHON_ERROR_HEADER_BACK = Back.LIGHTRED_EX
PYTHON_ERROR_HEADER_STYLE = Style.BRIGHT
PYTHON_STACKTRACE_STYLE = Style.DIM


# CMD Colors

COMMAND_NOT_FOUND_TEXT_STYLE = Style.DIM
COMMAND_NOT_FOUND_TEXT_FORE = Fore.YELLOW

SUGGEST_TEXT_STYLE = Style.BRIGHT
SUGGEST_TEXT_COLOR = Fore.CYAN
SUGGEST_ITEMS_STYLE = Fore.YELLOW

PROMPT_DEFAULT_TEXT = "#ffffff" #00ffff
PROMPT_NAME = "#009999"
PROMPT_SYMBOL = "#999966"


# Completion Colors

COMPLETION_COMMAND_NAME = 'ansiblue'
COMPLETION_COMMAND_DESCRIPTION = 'fg=\"#5f00d7\"'
COMPLETION_ROOT_COMMAND_NAME = 'ansiblue'
COMPLETION_ROOT_COMMAND_DESCRIPTION = 'fg=\"#5f00d7\"'

COMPLETION_CHOICE_DEFAULT = 'ansiblack'
COMPLETION_CHOICE_BOOLEAN_TRUE = 'ansigreen'
COMPLETION_CHOICE_BOOLEAN_FALSE = 'style fg=\"#dc322f\"'

COMPLETION_OPTION_NAME = 'ansibrightmagenta'
COMPLETION_OPTION_DESCRIPTION = 'fg=\"#5f00d7\"'

COMPLETION_ARGUMENT_NAME = 'ansired'
COMPLETION_ARGUMENT_DESCRIPTION = 'fg=\"#5f00d7\"'


# Base Shell Command Colors

SHELL_HISTORY_CLEARED_STYLE = Style.DIM
SHELL_HISTORY_CLEARED_TRUE = Fore.GREEN
SHELL_HISTORY_CLEARED_FALSE = Fore.RED + Style.BRIGHT


# Lexer Colors

PYGMENTS_NAME_HELP = '#afd700'
PYGMENTS_NAME_EXIT = '#ff005f'
PYGMENTS_NAME_SYMBOL = '#5faf87'

PYGMENTS_NAME_SHELL = '#5faf00'
PYGMENTS_NAME_COMMAND = '#afaf87'
PYGMENTS_NAME_SUBCOMMAND = '#5f5fff'
PYGMENTS_NAME_INVALIDCOMMAND = '#ff0000'

PYGMENTS_OPTION = '#d75f5f'

PYGMENTS_OPERATOR = '#ffaf00'
PYGMENTS_KEYWORD = '#af0087'

PYGMENTS_LITERAL_NUMBER = '#ffff5f'
PYGMENTS_LITERAL_STRING = '#8a380f'
PYGMENTS_LITERAL_STRING_LITERAL = '#1fad91'

PYGMENTS_PARAMETER_CHOICE = '#3385ff'