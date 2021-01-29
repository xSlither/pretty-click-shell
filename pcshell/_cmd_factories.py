import types
import logging
import shlex
import traceback

from functools import update_wrapper
from logging import NullHandler

import click
from click._compat import get_text_stderr
from click._bashcomplete import get_choices

from colorama import Fore, Back, Style

from ._cmd import ClickCmd
from ._utils import HasKey

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())


def get_invoke(cmd: click.Command):
    """
    Factory method for creating a command's main method (do_*) from the click command object
    """
    assert isinstance(cmd, click.Command)

    def invoke_(self, arg):
        try:
            # Invoke the command
            cmd.main(args=shlex.split(arg),
                         prog_name=cmd.name,
                         standalone_mode=False,
                         parent=self.ctx)

        except click.UsageError as e:
            # Shows the usage subclass error message
            file = get_text_stderr()

            color = None
            hint = ""
            if e.cmd is not None and e.cmd.get_help_option(e.ctx) is not None:
                hint = "\tTry '{} {}' for help.\n".format(
                    e.ctx.command_path, e.ctx.help_option_names[0]
                )
            if e.ctx is not None:
                print()
                color = e.ctx.color
                click.echo("\t{}\n{}".format(e.ctx.get_usage(), hint), file=file, color=color)

            click.echo("\t{err_color}Error: {msg}{reset}".format(err_color=Fore.RED, reset=Style.RESET_ALL, msg=e.format_message()), file=file)    

        except click.ClickException as e:
            # Shows the standard click exception message
            file = get_text_stderr()
            click.echo("\t{err_color}Error: {msg}{reset}".format(err_color=Fore.RED, reset=Style.RESET_ALL, msg=e.format_message()), file=file)

        except click.Abort:
            # An EOF or KeyboardInterrupt was returned
            # Raise as a new KeyboardInterrupt
            click.echo(file=self._stdout)
            raise KeyboardInterrupt()

        except SystemExit:
            # Ignore system exit from click
            pass

        except Exception as e:
            # Catch and pretty-format a Python Exception caught from the click command

            formatter = click.HelpFormatter(4, 128, 128)
            formatter.indent()

            formatter.write_text('{}An unexpected error has occurred{}'.format(Fore.YELLOW, Style.RESET_ALL))
            formatter.write_paragraph()

            with formatter.section('{fore}{back}{style}Python Stack Trace{reset}'.format(fore=Fore.WHITE, back=Back.RED, style=Style.BRIGHT, reset=Style.RESET_ALL)):
                formatter.write(Style.DIM)
                formatter.write_text(''.join(traceback.format_exception(type(e), e, None)))
                formatter.write(Style.RESET_ALL)

            click.echo(formatter.getvalue())
            logger.warning(traceback.format_exc())

        # Do not allow shell to exit
        return False

    invoke_ = update_wrapper(invoke_, cmd.callback)
    invoke_.__name__ = 'do_%s' % cmd.name
    return invoke_


def get_help(cmd: click.Command):
    """
    Factory method for creating a command's help method (help_*) from the click command object
    """
    assert isinstance(cmd, click.Command)

    def help_(self):
        extra = {}
        for key, value in cmd.context_settings.items():
            if key not in extra:
                extra[key] = value

        with click.Context(cmd, info_name=cmd.name, parent=self.ctx, **extra) as ctx:
            click.echo(ctx.get_help(), color=ctx.color)

    help_.__name__ = 'help_%s' % cmd.name
    return help_


def get_complete(command):
    """
    Factory method for creating a command's callback method (complete_*) from the click command object
    """
    assert isinstance(command, click.Command)

    def complete_(self, text, line, begidx, endidx):
        # Strip the command's name from the args
        args = shlex.split(line[:begidx])
        args = args[1:]

        # Delegate to click
        return [choice[0] if isinstance(choice, tuple) else choice
                for choice in get_choices(command, command.name, args, text)]

    complete_.__name__ = 'complete_%s' % command.name
    return complete_


# An implementation of ClickCmd that will use the factory methods to assign the command methods
class ClickCmdShell(ClickCmd):

    def __init__(self, ctx=None, on_finished=None, hist_file=None, add_command_callback=None, system_cmd=None, *args, **kwargs):
        self.add_command_callback = add_command_callback
        super(ClickCmdShell, self).__init__(ctx, on_finished, hist_file, system_cmd, *args, **kwargs)

    def add_command(self, cmd, name):
        setattr(self, 'do_%s' % name, types.MethodType(get_invoke(cmd), self))
        setattr(self, 'help_%s' % name, types.MethodType(get_help(cmd), self))
        setattr(self, 'complete_%s' % name, types.MethodType(get_complete(cmd), self))

        setattr(self, 'hidden_%s' % name, cmd.hidden)

        keys = dir(cmd)
        if 'alias' in keys:
            if not cmd.alias:
                setattr(self, 'orig_%s' % name, True)

        if self.add_command_callback:
            self.add_command_callback(self, cmd, name)