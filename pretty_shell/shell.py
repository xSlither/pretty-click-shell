import sys
from copy import deepcopy
from io import StringIO

import click
from click.core import MultiCommand, _check_multicommand

from . import cs_globs as globs
from .pretty import PrettyGroup, PrettyCommand
from .multicommand import CUSTOM_COMMAND_PROPS
from .utils import HasKey
from ._cmd_factories import ClickCmdShell


class Shell(PrettyGroup):

    def __init__(self, isShell=False, prompt=None, intro=None, hist_file=None, 
    on_finished=None, add_command_callback=None, 
    system_cmd=lambda: 'color 0a' if platform.system() == 'Windows' else '', 
    **attrs):
        # Allows this class to be used as a subclass without a new shell instance attached
        self.isShell = isShell

        if isShell:
            attrs['invoke_without_command'] = True
            super(Shell, self).__init__(**attrs)

            # Create the shell
            self.shell = ClickCmdShell(hist_file=hist_file, on_finished=on_finished, add_command_callback=add_command_callback, system_cmd=system_cmd)
            if prompt:
                self.shell.prompt = prompt
            self.shell.intro = intro

        else:
            super(Shell, self).__init__(**attrs)


    def add_command(self, cmd: click.Command, name=None):
        name = name or cmd.name
        if name is None: raise TypeError("Command has no name.")

        _check_multicommand(self, name, cmd, register=True)

        if type(name) is str:
            self.commands[name] = cmd
        else:
            for _name_ in name:
                self.commands[_name_] = cmd

        if self.isShell: self.shell.add_command(cmd, name)


    def invoke(self, ctx: click.Context):
        if self.isShell:
            ret = super(Shell, self).invoke(ctx)
            if not ctx.protected_args and not ctx.invoked_subcommand:
                ctx.info_name = None
                self.shell.ctx = ctx
                return self.shell.cmdloop()
            return ret
        else:
            return MultiCommand.invoke(self, ctx)

    
class MultiCommandShell(Shell):

    def __init__(self, **attrs):
        super(MultiCommandShell, self).__init__(**attrs)
        if self.isShell: BaseShellCommands.addAll(self)


    @staticmethod
    def __strip_invalidKeys(kwargs):
        for _kwarg_ in CUSTOM_COMMAND_PROPS:
            if HasKey(_kwarg_, kwargs):
                kwargs.pop(_kwarg_, None)

    @staticmethod
    def __assign_invalidKeys(kwargs, cmd):
        for _kwarg_ in CUSTOM_COMMAND_PROPS:
            if HasKey(_kwarg_, kwargs):
                setattr(cmd, _kwarg_, kwargs[_kwarg_])


    def command(self, *args, **kwargs):
        """Behaves the same as `click.Group.command()` except if passed
        a list of names, all after the first will be aliases for the first.
        Also allows for use of custom kwargs defined in multicommand.py.
        """
        def decorator(f):
            old_kwargs = kwargs.copy()
            self.__strip_invalidKeys(kwargs)

            from .pretty import prettyCommand

            tmpCommand = None
            origHelpTxt = None
            try:
                if isinstance(args[0], list):
                    _args = [args[0][0]] + list(args[1:])
                    for alias in args[0][1:]:
                        if tmpCommand is None:
                            cmd: PrettyCommand = prettyCommand(alias, None, **kwargs)(f)
                            origHelpTxt = cmd.help
                            cmd.help = "(Alias for '{c}') {h}".format(c = _args[0], h = cmd.help)
                            cmd.short_help = "Alias for '{}'".format(_args[0])
                            cmd.true_hidden = cmd.hidden
                            cmd.hidden = True
                            self.__assign_invalidKeys(old_kwargs, cmd)
                            super(MultiCommandShell, self).add_command(cmd)
                            tmpCommand = cmd

                        else:
                            cmd = deepcopy(tmpCommand)
                            cmd.name = alias
                            cmd.help = "(Alias for '{c}') {h}".format(c = _args[0], h = origHelpTxt)
                            cmd.short_help = "Alias for '{}'".format(_args[0])
                            cmd.hidden = True
                            self.__assign_invalidKeys(old_kwargs, cmd)
                            super(MultiCommandShell, self).add_command(cmd)
                else:
                    _args = args


                if tmpCommand is None:
                    cmd: PrettyCommand = prettyCommand(*_args, **kwargs)(f)
                    self.__assign_invalidKeys(old_kwargs, cmd)
                    super(MultiCommandShell, self).add_command(cmd)
                    return cmd

                else:
                    cmd = deepcopy(tmpCommand)
                    cmd.name = _args[0]
                    cmd.help = origHelpTxt
                    cmd.short_help = ''
                    cmd.hidden = cmd.true_hidden
                    self.__assign_invalidKeys(old_kwargs, cmd)
                    super(MultiCommandShell, self).add_command(cmd)
                    return cmd

            except:
                cmd: PrettyCommand = prettyCommand(*args, **kwargs)(f)
                self.__assign_invalidKeys(old_kwargs, cmd)
                super(MultiCommandShell, self).add_command(cmd)
                return cmd

        return decorator


class BaseShellCommands:

    @staticmethod
    def addAll(shell: MultiCommandShell):

        @shell.command(['help', 'h', '--help'], hidden=True)
        def __get_help__():
            with click.Context(shell) as ctx:
                click.echo(shell.get_help(ctx))

        @shell.command(['cls', 'clear'], hidden=True)
        def cls():
            """Clears the Terminal"""
            click.clear()

        @shell.command(['q', 'quit'], hidden=True, exit=True)
        def _exit_():
            """Exits the Shell"""
            pass

        @shell.command(['exit'], exit=True)
        def __exit__():
            """Exits the Shell"""
            pass

        @shell.command(['repeat'], hidden=True)
        def __repeat_command__():
            """Repeats the last valid command with all previous parameters"""
            if globs.__LAST_COMMAND__:
                globs.__IS_REPEAT__ = True
                globs.__PREV_STDIN__ = sys.stdin
                sys.stdin = StringIO(globs.__LAST_COMMAND__)