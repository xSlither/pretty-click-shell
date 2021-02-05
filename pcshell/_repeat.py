import click

from . import globals as globs
from .types import HiddenPassword


def BuildCommandString(ctx: click.Context) -> None:
    if globs.__IsShell__ and not globs.__IS_REPEAT__:
        ret = ctx.command_path
        globs.__LAST_COMMAND_VISIBLE__ = ret

        args = { a.name: a for a in ctx.command.params if isinstance(a, click.Argument) }
        opts = { o.name: o for o in ctx.command.params if isinstance(o, click.Option) }

        if ctx.params and len(ctx.params) > 0:
            for key in ctx.params:
                if isinstance(ctx.params[key], bool):
                    if not key in args:
                        if ctx.params[key]: 
                            ret += ' --{key}'.format(key=key)
                            if key in opts:
                                if not (opts[key].is_bool_flag or opts[key].is_flag):
                                    ret += ' %s' % ctx.params[key]
                    else: ret += ' {value}'.format(value=ctx.params[key])

                elif isinstance(ctx.params[key], str):
                    if not key in args:
                        if ctx.params[key]:
                            ret += ' --{key} {value}'.format(key=key, value=ctx.params[key])
                        else: ret += ' --{key} ""'.format(key=key)
                    else: ret += ' {value}'.format(value=ctx.params[key])

                elif isinstance(ctx.params[key], HiddenPassword):
                    if not key in args:
                        if ctx.params[key].password:
                            ret += ' --{key} {value}'.format(key=key, value=ctx.params[key].password)
                        else: ret += ' --{key} ""'.format(key=key)
                    else: ret += ' {value}'.format(value=ctx.params[key].password)

        globs.__LAST_COMMAND__ = ret