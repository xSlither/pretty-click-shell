#  ANCHOR References

import os
import sys # REQUIRED
import platform
import datetime

import click # REQUIRED
import pcshell # REQUIRED

from ._settings import ToggleFlag, print_all_settings, SETTINGS



#==============================================================================
#  ANCHOR Global Shell Info

__version__ = '1.0.0.0'

pcshell.globals.__IsShell__ = len(sys.argv) == 1 # REQUIRED
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
__SHELL_INTRO__ = '\nPython Version: {pyVer}\nClick Version: {clVer}\n\n{header}\nTest Application Shell - v.{ver}\n{footer}\n'.format(
    pyVer=platform.python_version(), clVer=click.__version__, ver=__version__,
    header=__SHELL_HEADER__, footer=__SHELL_FOOTER__
)


#---------------------------------------------------------------------------------------------
@pcshell.shell(prompt = 'testapp > ', intro = pcshell.chars.CLEAR_CONSOLE + __SHELL_INTRO__, context_settings = CONTEXT_SETTINGS)
def testapp():
    """The Test Shell Application"""
    pass
#---------------------------------------------------------------------------------------------


#  ANCHOR General Option Presets

_option_useDevRegion = [
    click.option('--dev', is_flag=True, is_eager=True, prompt=False, help='Flag indicating to use the dev region')
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

@testapp.command(['enable'])
@pcshell.argument('singleflag', type=str, default='')
@pcshell.option('-f', '--flag', multiple=True, default=[''])
def __enable__(singleflag, flag):
    """Enable settings for the shell"""
    ToggleFlag(singleflag, flag, True)

@testapp.command(['disable'])
@pcshell.argument('singleflag', type=str, default='')
@pcshell.option('-f', '--flag', multiple=True, default=[''])
def __disable__(singleflag, flag):
    """Disable settings for the shell"""
    ToggleFlag(singleflag, flag, False)


# ANCHOR Command Trees

@testapp.group(context_settings=CONTEXT_SETTINGS)
def api():
    """Commands for invoking various API endpoints"""

@testapp.group(cls=pcshell.MultiCommandShell, isShell=True, 
prompt = 'someshell > ', intro=pcshell.chars.IGNORE_LINE, system_cmd=None, 
context_settings=CONTEXT_SETTINGS)
def someshell():
    """Some sub-shell application"""


# !SECTION
# --------------------------------------------


#--------------------------------------------
#  ANCHOR Command Tree | api -> x
#--------------------------------------------



#--------------------------------------------


# !SECTION
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


# ANCHOR Main Routine

if __name__ == '__main__':
    try: testapp()
    except Exception as e: 
        print(str(e)) 
    finally: print('')