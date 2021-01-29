import click
from pcshell import utils

from colorama import Fore, Style


SETTINGS = {}

__SHELL_FLAGS_DETAILS__ = [
    ['ShowTokens', 'Reveal session tokens & keys in displayed responses'],
    ['VerboseResponses', 'Sets the maximum verbosity level for all responses'],
    ['HideResponse', 'Does not output any responses to the console'],
    ['UseDefaultCreds', 'Requests will use default credentials when applicable'],
    ['SkipValidation', 'Skip validation on all responses'],
    ['LogDebugInfo', 'Log all debug information for the session'],
    ['Pager', 'Will display responses using a pager when a character limit is exceeded'],
]

def _initFlags():
    ret = ['']
    details = sorted(__SHELL_FLAGS_DETAILS__, key=lambda d: d[0])
    for detail in details: ret.append(detail[0].lower())
    return ret

SHELL_FLAGS = click.Choice(_initFlags())


def print_all_settings():
    details = sorted(__SHELL_FLAGS_DETAILS__, key=lambda d: d[0])
    for detail in details:
        print_setting(detail[0], SETTINGS[detail[0].lower()] if utils.HasKey(detail[0].lower(), SETTINGS) else False, detail[1])


def ToggleFlag(singleflag: str, flag: str, enable: bool):
    def _ToggleFlag(flag: str, value: bool) -> None:
        global SETTINGS

        flag = flag.lower()
        print()

        if not flag:
            click.echo('\t{}{}{}'.format(Style.DIM, 'No flag provided', Style.RESET_ALL))
            return

        if flag in SHELL_FLAGS.choices:
            for detail in __SHELL_FLAGS_DETAILS__:
                if flag == detail[0].lower():
                    SETTINGS[flag] = value
                    break
        else:
            s = utils.suggest(SHELL_FLAGS.choices, flag)
            click.echo('\t{}{}{}'.format(Fore.YELLOW, 'Flag "{}" does not exist{}'.format(
            flag,
            '. Did you mean "{}"?'.format(s) if s else '',
            ), Style.RESET_ALL))
            return

        click.echo('\t{}Flag "{}" was {}{}{}'.format(Style.DIM, flag, Fore.GREEN if value else Fore.RED, 'enabled' if value else 'disabled', Style.RESET_ALL))

    if singleflag != '': 
        _ToggleFlag(singleflag, enable)
        return

    if flag and flag[0] != '':
        for _flag_ in flag:
            if _flag_ != '': _ToggleFlag(_flag_, enable)
    elif flag:
        _ToggleFlag(flag[0], enable)


def print_setting(name, value, desc) -> None:
    prop = '\t{prop_color}{name}{reset}:'.format(
        prop_color=Fore.YELLOW, name=name, reset=Style.RESET_ALL
    )

    val = '\t{value_color}{value}{reset}'.format(
        reset=Style.RESET_ALL,
        value_color= Fore.GREEN if value else Fore.RED,
        value= 'Enabled' if value else 'Disabled'
    )

    print()
    click.echo('{:<40s}{:>}'.format(prop, val))
    print()
    click.echo('\t\t{dim}{desc}{reset}'.format(dim= Style.DIM, desc=desc, reset= Style.RESET_ALL))