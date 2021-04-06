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

                # Boolean Parameter
                if isinstance(ctx.params[key], bool):
                    if not key in args:
                        if ctx.params[key]: 
                            ret += ' --{key}'.format(key=key)
                            if key in opts:
                                if not (opts[key].is_bool_flag or opts[key].is_flag):
                                    ret += ' %s' % ctx.params[key]
                    else: ret += ' {value}'.format(value=ctx.params[key])

                # String Parameter
                elif isinstance(ctx.params[key], str):
                    if not key in args:
                        if ctx.params[key]:
                            ret += ' --{key} {value}'.format(key=key, value=ctx.params[key])
                        else: ret += ' --{key} ""'.format(key=key)
                    else: ret += ' "{value}"'.format(value=ctx.params[key])

                # Integer Parameter
                elif isinstance(ctx.params[key], int):
                    if not key in args:
                        if ctx.params[key]:
                            ret += ' --{key} {value}'.format(key=key, value=ctx.params[key])
                        else: ret += ' --{key} 0'.format(key=key)
                    else: ret += ' {value}'.format(value=ctx.params[key])

                # Float Parameter
                elif isinstance(ctx.params[key], float):
                    if not key in args:
                        if ctx.params[key]:
                            ret += ' --{key} {value}'.format(key=key, value=ctx.params[key])
                        else: ret += ' --{key} 0.0'.format(key=key)
                    else: ret += ' {value}'.format(value=ctx.params[key])

                # Password Parameter
                elif isinstance(ctx.params[key], HiddenPassword):
                    if not key in args:
                        if ctx.params[key].password:
                            ret += ' --{key} {value}'.format(key=key, value=ctx.params[key].password)
                        else: ret += ' --{key} ""'.format(key=key)
                    else: ret += ' {value}'.format(value=ctx.params[key].password)

                # Typed Tuple List Parameter
                elif isinstance(ctx.params[key], list):
                    def convert_list(lst=ctx.params[key]):
                        return [
                            str(i) if not type(i) == str and not type(i) == bool 
                                else '"%s"' % str(i) if type(i) == str 
                                    else str(i).lower() 
                            for i in lst
                        ]

                    def add_typed_tuple_param(lst=convert_list(), root=ctx.params[key]):
                        ret = ''
                        if not key in args:
                            if root:
                                ret += ' --{key} [{value}]'.format(key=key, value=', '.join(lst))
                            else: ret += ' --{key} []'.format(key=key)
                        else: ret += ' [{value}]'.format(value=', '.join(lst))
                        return ret

                    if not isinstance(ctx.params[key][0], list): 
                        ret += add_typed_tuple_param()
                    else:
                        for item in ctx.params[key]:
                            tup = convert_list(item)
                            ret += add_typed_tuple_param(tup, item)

                # Click Tuple Parameter
                elif isinstance(ctx.params[key], tuple):
                    isArg = not key in args

                    def add_click_tuple_param(lst=ctx.params[key]):
                        ret = ' --{key}'.format(key=key)
                        for val in lst:
                            if not isArg:
                                if val:
                                    ret += ' {value}'.format(value=val)
                                else:
                                    if isinstance(val, str):
                                        ret += ' ""'
                                    else: ret += ' null'
                            else:
                                if isinstance(val, str):
                                    ret += ' "{value}"'.format(value=val)
                                else: ret += ' {value}'.format(value=val)
                        return ret

                    if not isinstance(ctx.params[key][0], tuple):
                        ret += add_click_tuple_param()
                    else:
                        for val in ctx.params[key]:
                            ret += add_click_tuple_param(val)


        globs.__LAST_COMMAND__ = ret