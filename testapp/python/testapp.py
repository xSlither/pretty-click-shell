#  ANCHOR Module References

from typing import List

import os
import sys
import platform
import datetime

import click
import pcshell # REQUIRED
import prompt_toolkit


# Local Imports

try:
    from ._settings import ToggleFlag, print_all_settings, SETTINGS, SHELL_FLAGS
except:
    from _settings import ToggleFlag, print_all_settings, SETTINGS, SHELL_FLAGS



#==============================================================================
#  ANCHOR Global Shell Info

__version__ = '1.0.0.0'

pcshell.globals.HISTORY_FILENAME = '.testapp-history'

pcshell.colors.COMPLETION_ROOT_COMMAND_DESCRIPTION = 'fg=\"#b30000\"'

IsShell = pcshell.globals.__IsShell__
#==============================================================================



#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#============================================
#  SECTION Click CLI Implementation
#============================================

#  ANCHOR Shell Configuration

CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)

__SHELL_HEADER__ = '=' * 44
__SHELL_FOOTER__ = '=' * 44
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

@testapp.group(cls=pcshell.MultiCommandShell, context_settings=CONTEXT_SETTINGS)
def multi():
    """Some Test commands w/ Aliases & multiples"""


# Sub Shell - SomeShell

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

@api.group(context_settings=CONTEXT_SETTINGS)
def another():
    """A sub-group of the API Group"""


@api.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@pcshell.argument('arg1', type=str, help="Some argument for this command")
@pcshell.option('--opt1', type=pcshell.types.Choice(['blue', 'red'], display_tags=['ansiblue', 'style fg="#dc322f"']), help="Some option for this command")
@pcshell.option('--opt2', type=bool, help="Some option for this command")
@pcshell.repeatable
def test(arg1, opt1, opt2):
    """Some API Command"""
    if IsShell: click.echo('Argument was "{}". "{}" was selected, with additional flag = "{}"'.format(arg1, opt1, opt2))
    return { 'someProp': arg1, 'someProp2': opt1, 'someProp3': opt2 }

@api.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=False)
@pcshell.option('--date', type=str, callback=VerifyDate, prompt='Effective Date', help="A MM/DD/YY Date Parameter")
@pcshell.add_options(option_useDevRegion)
@pcshell.repeatable
def test2(date, dev):
    """Some Other API Command"""
    if IsShell: click.echo('Effective Date was "{}", and DEV Mode = "{}"'.format(date, dev))
    return { 'date': date, 'devMode': dev }

#--------------------------------------------


#--------------------------------------------
#  ANCHOR Command Tree | api -> another -> x
#--------------------------------------------

@another.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@pcshell.argument('test', type=str, help='A string argument')
@pcshell.argument('test2', type=int, help='An int argument')
@pcshell.argument('test3', type=float, help='A float argument')
@pcshell.option('--opt1', type=pcshell.types.Choice(['blue', 'red'], display_tags=['ansiblue', 'style fg="#dc322f"']), help="Some option for this command")
@pcshell.option('--opt2', type=str, help='Some string option', default='test')
@pcshell.add_options(option_useDevRegion)
def test(test, test2, test3, opt1, opt2, dev):
    """Some Other Api Command"""
    if IsShell: click.echo('Provided Parameter of "{}"'.format(opt1))
    return { 'someProp': opt1 }

#--------------------------------------------


#--------------------------------------------
#  ANCHOR Command Tree | multi -> x
#--------------------------------------------

tuple_test_choice = pcshell.types.Choice(['choice1', 'choice2'], display_tags=['style fg=#d7ff00'])

@multi.command(['tup', 'tuple'], context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@pcshell.option('--t', default=[], literal_tuple_type=[str, float, bool, tuple_test_choice], help='A typed tuple literal option')
@pcshell.option('--c', default=[], literal_tuple_type=[bool, bool], help='A second typed tuple literal option', multiple=True)
@pcshell.argument('test', type=str, help='A string argument')
@pcshell.argument('test2', type=int, help='An int argument')
@pcshell.argument('test3', type=float, help='A float argument')
@pcshell.add_options(option_useDevRegion)
@pcshell.repeatable
def test_tuple(t, test, test2, test3, c, dev):
    """Test Literal Tuple Completion"""
    if IsShell:
        if t:
            click.echo('\n\tProvided Optional Tuple 1: %s' % str(t))
            click.echo('\tOptional Tuple Type is: %s' % type(t))
        if c:
            click.echo('\n\tProvided Optional Tuple 2: %s' % str(c))
            click.echo('\tOptional Tuple Type is: %s' % type(c))
        click.echo('\n\tArgument 1: %s' % test)
        click.echo('\tArgument 2: %s' % test2)
        click.echo('\tArgument 3: %s' % test3)
        if dev: click.echo('\n\tDEV MODE = TRUE')
    return t

@multi.command(['click_tuple', 'clicktup'], context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@pcshell.option('--t', default=(None, None), type=(str, tuple_test_choice), help='A click tuple type option', multiple=True)
@pcshell.argument('test', type=int, help='An integer argument')
@pcshell.repeatable
def test_click_tuple(test, t):
    """Test Click Tuple Completion"""
    if IsShell:
        click.echo('\n\tProvided Tuple: %s' % str(t))
        click.echo('\tTuple Type is: %s' % type(t))
        click.echo('\n\tProvided Argument: %s' % test)
    return t

@multi.command(['tuple_args', 'tuparg'], context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@pcshell.option('--t', default=[], literal_tuple_type=[bool, bool], help='A typed tuple option')
@pcshell.argument('test', type=(tuple_test_choice, bool), help='A click tuple type argument')
@pcshell.argument('test2', type=float, help='A float argument')
@pcshell.repeatable
def test_arg_tuples(test, test2, t):
    """Test Tuple Argument Completion"""
    if IsShell:
        click.echo('\n\tProvided Tuple: %s' % str(t))
        click.echo('\tTuple Type is: %s' % type(t))
        click.echo('\n\tProvided Argument1: %s' % str(test))
        click.echo('\tProvided Argument2: %s' % str(test2))
    return test


#--------------------------------------------


#--------------------------------------------
#  ANCHOR Command Tree | someshell -> x
#--------------------------------------------

def some_callback(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing: return False
    if IsShell: click.echo('[Option 2 Callback] (Is Eager)')
    return value

def some_other_callback(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing: return False
    if IsShell: click.echo('[Option 1 Callback]')
    return value

@someshell.command(context_settings=CONTEXT_SETTINGS)
@pcshell.option('--opt1', is_flag=True, callback=some_other_callback, help='Some Flag')
@pcshell.option('--opt2', is_flag=True, is_eager=True, hidden=True, callback=some_callback, help='This help text should never be displayed')
@pcshell.repeatable
def test(opt1, opt2):
    """Some Sub-Shell Command"""
    if IsShell:
        click.echo('Option 1 is: %s' % opt1)
        click.echo('Option 2 is: %s' % opt2)
    return { 'opt1': opt1, 'opt2': opt2 }


@someshell.group(context_settings=CONTEXT_SETTINGS)
def group():
    """A Command Group in the Sub-Shell"""


@group.command(context_settings=CONTEXT_SETTINGS)
@pcshell.argument('choice', type=pcshell.types.Choice(['blue', 'red'], display_tags=['ansiblue', 'ansired']))
@pcshell.repeatable
def cmd(choice):
    """Some Sub-Command of the Sub-Shell"""
    if IsShell: click.echo('Argument was: "%s"' % choice)
    return 'Some return string that includes "%s"' % choice

#--------------------------------------------


# !SECTION
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



# ANCHOR Main Routine

if __name__ == '__main__':
    testapp()