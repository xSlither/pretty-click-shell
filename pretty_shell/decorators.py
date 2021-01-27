from functools import update_wrapper

import click

from .shell import Shell
from ._repeat import BuildCommandString

from .pretty import argument


def add_options(*options):
    """Appends a variadic array of click.option arrays to the command (in reverse order)
    """
    def _add_options(func):
        for _option_ in options:
            for option in reversed(_option_):
                func = option(func)
        return func
    return _add_options


def shell(name=None, **attrs):
    """Instantiates a new Shell instance, using the default subclass. 
    
    Functions similar to @click.command(). Use this decorator on your top-level command for your click project
    """
    attrs.setdefault('cls', Shell)
    return click.command(name, isShell=True, **attrs)


def repeatable(f):
    """Captures the current context and allows it to be repeated using the "repeat" command.
    \nPlace this decorator beneath all other click decorators, or the context will not be accurate
    """
    def repeat(*args, **kwargs):
        ctx = click.get_current_context()
        BuildCommandString(ctx)
        return f(*args, **kwargs)

    return update_wrapper(repeat, f)