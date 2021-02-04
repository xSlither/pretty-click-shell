#  ANCHOR References

import os
import sys # REQUIRED
import platform
import datetime

import click
import pcshell # REQUIRED
import prompt_toolkit

from ._settings import ToggleFlag, print_all_settings, SETTINGS, SHELL_FLAGS



#==============================================================================
#  ANCHOR Global Shell Info

__version__ = '1.0.0.0'

pcshell.globals.__IsShell__ = len(sys.argv) == 1 # REQUIRED
pcshell.globals.HISTORY_FILENAME = '.testapp-history'

pcshell.colors.COMPLETION_ROOT_COMMAND_DESCRIPTION = 'fg=\"#b30000\"'
#==============================================================================



#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#============================================
#  SECTION Click CLI Implementation
#============================================

#  ANCHOR Shell Configuration

CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)

__SHELL_HEADER__ = '============================================'
__SHELL_FOOTER__ = '============================================'
__SHELL_INTRO__ = '\nPython Version: {pyVer}\nClick Version: {clVer}\nPrompt Toolkit Version: {ptVer}\n\n{header}\nTest Application Shell - v.{ver}\n{footer}\n'.format(
    pyVer=platform.python_version(), clVer=click.__version__, ver=__version__, ptVer=prompt_toolkit.__version__,
    header=__SHELL_HEADER__, footer=__SHELL_FOOTER__
)


def ShellStart():
    if platform.system() == 'Windows':
        os.system('color 0a')


#---------------------------------------------------------------------------------------------
@pcshell.shell(prompt = 'testapp', intro = pcshell.chars.CLEAR_CONSOLE + __SHELL_INTRO__, 
before_start=ShellStart, context_settings = CONTEXT_SETTINGS)
def testapp():
    """The Test Shell Application"""
    pass
#---------------------------------------------------------------------------------------------


#  ANCHOR General Option Presets

option_useDevRegion = [
    pcshell.option('--dev', is_flag=True, is_eager=True, prompt=False, help='Flag indicating to use the dev region')
]


#  ANCHOR General Parameter Callbacks

def VerifyDate(ctx: click.Context, param, value: str) -> str:
    if not value:
        if not ctx.resilient_parsing:
            click.secho('Date cannot be null')
            ctx.exit()
        else: return value
    
    try:
        datetime.datetime.strptime(value, '%m/%d/%Y')
    except ValueError:
        click.secho('Date is invalid. Expected MM/DD/YYYY')
        ctx.exit()
    return value


#--------------------------------------------
#  SECTION Command Tree | ROOT -> x
#--------------------------------------------

# ANCHOR Setting Commands

@testapp.command(['settings'])
def __print_settings__():
    """Lists all of the settings & their current value"""
    print_all_settings()


option_toggable_flags = [
    pcshell.option('-f', '--flag', choices=SHELL_FLAGS, multiple=True, is_eager=True, 
        default=[''], help='(Multiple) Use the --flag options to toggle set multiple flags at once')
]


@testapp.command(['enable'])
@pcshell.argument('singleflag', type=str, choices=SHELL_FLAGS, default='')
@pcshell.add_options(option_toggable_flags)
def __enable__(singleflag, flag):
    """Enable settings for the shell"""
    ToggleFlag(singleflag, flag, True)

@testapp.command(['disable'])
@pcshell.argument('singleflag', type=str, choices=SHELL_FLAGS, default='')
@pcshell.add_options(option_toggable_flags)
def __disable__(singleflag, flag):
    """Disable settings for the shell"""
    ToggleFlag(singleflag, flag, False)


# ANCHOR Command Trees

@testapp.group(context_settings=CONTEXT_SETTINGS)
def api():
    """Commands for invoking various API endpoints"""


__someshell_version__ = '1.0.0.5'

def print_someshell_version(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing: return
    click.echo(__someshell_version__)
    ctx.exit()

@testapp.new_shell(prompt = 'someshell', intro=pcshell.chars.IGNORE_LINE,
before_start=None, context_settings=CONTEXT_SETTINGS,
hist_file=os.path.join(os.path.expanduser('~'), '.testapp-someshell-history'))
@pcshell.option('--version', is_flag=True, callback=print_someshell_version, expose_value=False, is_eager=True, hidden=True)
def someshell():
    """Some sub-shell application"""


# !SECTION
# --------------------------------------------


#--------------------------------------------
#  ANCHOR Command Tree | api -> x
#--------------------------------------------

@api.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@pcshell.argument('arg1', type=str, help="Some argument for this command")
@pcshell.option('--opt1', type=pcshell.types.Choice(['blue', 'red'], display_tags=['ansiblue', 'ansired']), help="Some option for this command")
@pcshell.option('--opt2', type=bool, help="Some option for this command")
def test(arg1, opt1, opt2):
    """Some API Command"""
    click.echo('Argument was "{}". "{}" was selected, with additional flag = "{}"'.format(arg1, opt1, opt2))
    pass

@api.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=False)
@pcshell.option('--date', type=str, callback=VerifyDate, prompt='Effective Date', help="Some argument for this command")
@pcshell.add_options(option_useDevRegion)
def test2(date, dev):
    """Some Other API Command"""
    click.echo('Effective Date was "{}", and DEV Mode = "{}"'.format(date, dev))
    pass

#--------------------------------------------


#--------------------------------------------
#  ANCHOR Command Tree | someshell -> x
#--------------------------------------------

def some_callback(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing: return False
    click.echo('[Option 2 Callback] (Is Eager)')
    return value

def some_other_callback(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing: return False
    click.echo('[Option 1 Callback]')
    return value

@someshell.command(context_settings=CONTEXT_SETTINGS)
@pcshell.option('--opt1', is_flag=True, callback=some_other_callback, help='Some Flag')
@pcshell.option('--opt2', is_flag=True, is_eager=True, hidden=True, callback=some_callback, help='This help text should never be displayed')
def test(opt1, opt2):
    """Some Sub-Shell Command"""
    click.echo('Option 1 is: %s' % opt1)
    click.echo('Option 2 is: %s' % opt2)
    pass


@someshell.group(context_settings=CONTEXT_SETTINGS)
def group():
    """A Command Group in the Sub-Shell"""


@group.command(context_settings=CONTEXT_SETTINGS)
@pcshell.argument('choice', type=pcshell.types.Choice(['blue', 'red'], display_tags=['ansiblue', 'ansired']))
def cmd(choice):
    """Some Sub-Command of the Sub-Shell"""
    click.echo('Argument was: "%s"' % choice)

#--------------------------------------------


# !SECTION
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


# ANCHOR Main Routine

if __name__ == '__main__':
    try: testapp()
    except Exception as e: 
        print(str(e)) 
    finally: print('')