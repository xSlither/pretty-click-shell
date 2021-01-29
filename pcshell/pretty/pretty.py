import os
import sys
import json

import click
from click.core import (
    Command, Context, Argument, HelpFormatter, DEPRECATED_HELP_NOTICE,
    PY2, _verify_python3_env, _check_for_unicode_literals, get_os_args, 
    make_str, echo, _bashcomplete, Abort, Exit, ClickException, errno, 
    PacifyFlushWrapper
)

from colorama import Fore, Back, Style

from .. import globals as globs


class PrettyHelper:
    @staticmethod
    def get_help(self: Command, ctx: Context):
        """Formats the help into a string and returns it.
        """
        print()
        formatter = ctx.make_formatter()
        self.format_help(ctx, formatter)
        txt = formatter.getvalue().rstrip("\n")
        return '\t' + '\t'.join(txt.splitlines(True))

    @staticmethod
    def format_usage(self: Command, ctx: Context, formatter: HelpFormatter):
        """Writes the usage line into the formatter.
        """
        pieces = self.collect_usage_pieces(ctx)
        formatter.write_usage(ctx.command_path, '{style}{fore}{txt}{reset}'.format(style=Style.BRIGHT, fore=Fore.GREEN, txt=" ".join(pieces), reset=Style.RESET_ALL))

    @staticmethod
    def format_help_text(self: Command, ctx: Context, formatter: HelpFormatter):
        """Writes the help text to the formatter if it exists."""
        if self.help:
            formatter.write_paragraph()
            with formatter.indentation():
                help_text = '{fore}{help}{reset}'.format(fore=Style.DIM, help=self.help, reset=Style.RESET_ALL)
                if self.deprecated:
                    help_text += DEPRECATED_HELP_NOTICE
                formatter.write_text(help_text)
                formatter.write_paragraph()
        elif self.deprecated:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(DEPRECATED_HELP_NOTICE)

    @staticmethod
    def format_options(self: Command, ctx: Context, formatter: HelpFormatter):
        """Writes all the arguments & options into the formatter, if they exist."""
        opts = []
        args = []

        for param in self.get_params(ctx):
            help_record = param.get_help_record(ctx)

            if help_record:
                if not isinstance(param, Argument):
                    rv = '{style}{txt}{reset}'.format(style=Style.DIM, txt=help_record[1], reset=Style.RESET_ALL)
                    if rv is not None:
                        name = '{style}{txt}{reset}'.format(txt='--' + param.name, style=Fore.YELLOW, reset=Style.RESET_ALL)
                        opts.append((name, rv))

                else:
                    rv = '{style}{txt}{reset}'.format(style=Style.DIM, txt=help_record, reset=Style.RESET_ALL)
                    if rv is not None:
                        name = '{style}{txt}{reset}: {class_color}{type}{arrow_color} ->{reset}'.format(
                            txt=param.name, style=Fore.YELLOW+Style.BRIGHT, reset=Style.RESET_ALL,
                            class_color=Fore.CYAN, arrow_color=Fore.RED, type=param.type.name
                        )
                        args.append((name, rv))

        if args:
            with formatter.section('{fore}{back}{style}Arguments{reset}'.format(fore=Fore.WHITE, back=Back.RED, style=Style.BRIGHT, reset=Style.RESET_ALL)):
                formatter.write_dl(args)
                formatter.write_paragraph()

        if opts:
            with formatter.section('{fore}{back}{style}Options{reset}'.format(fore=Fore.WHITE, back=Back.MAGENTA, style=Style.BRIGHT, reset=Style.RESET_ALL)):
                formatter.write_dl(opts)

        self.format_commands(ctx, formatter)

    @staticmethod
    def format_commands(self: Command, ctx: Context, formatter: HelpFormatter):
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None: continue
            if cmd.hidden: continue

            commands.append((subcommand, cmd))

        formatter.width += 3
        if len(commands):
            limit = (formatter.width - 6 - max(len(cmd[0]) for cmd in commands))

            rows = []
            for subcommand, cmd in commands:
                help = '{style}{txt}{reset}'.format(txt=cmd.get_short_help_str(limit), style=Style.DIM, reset=Style.RESET_ALL)
                rows.append(('{style}{txt}{reset}'.format(txt=subcommand, style=Fore.YELLOW, reset=Style.RESET_ALL), help))

            if rows:
                formatter.write_paragraph()
                with formatter.section('{fore}{back}{style}Commands{reset}'.format(fore=Fore.WHITE, back=Back.BLUE, style=Style.BRIGHT, reset=Style.RESET_ALL)):
                    formatter.write_dl(rows)

    @staticmethod
    def format_epilog(self: Command, ctx: Context, formatter: HelpFormatter):
        """Additional formatting after all of the help text is written"""
        if self.epilog:
            formatter.write_paragraph()
            for line in self.epilog.split('\n'):
                formatter.write_text(line)


    @staticmethod
    def StdOut(ret: object) :
        if not globs.__IsShell__:
            try:
                return click.echo((json.dumps(ret, sort_keys=True)).strip())
            except:
                return click.echo(ret.strip())


    @staticmethod
    def main(self: Command, args=None, prog_name=None, complete_var=None, standalone_mode=True, **extra):
        """This is the way to invoke a script with all the bells and
        whistles as a command line application.  This will always terminate
        the application after a call.  If this is not wanted, ``SystemExit``
        needs to be caught.
        """
        # If we are in Python 3, we will verify that the environment is
        # sane at this point or reject further execution to avoid a
        # broken script.
        if not PY2:  _verify_python3_env()
        else: _check_for_unicode_literals()

        if args is None: args = get_os_args()
        else: args = list(args)

        if prog_name is None:
            prog_name = make_str(os.path.basename(sys.argv[0] if sys.argv else __file__))

        # Hook for the Bash completion
        _bashcomplete(self, prog_name, complete_var)

        try:
            try:
                with self.make_context(prog_name, args, **extra) as ctx:
                    rv = self.invoke(ctx)

                    # Send returned data from command to stdout if not in Shell mode, 
                    # automatically dumping the json of serializable objects
                    if rv: PrettyHelper.StdOut(rv)

                    if not standalone_mode:
                        return rv
                    ctx.exit()

            except (EOFError, KeyboardInterrupt):
                echo(file=sys.stderr)
                raise Abort()

            except ClickException as e:
                if not standalone_mode:
                    raise
                e.show()
                sys.exit(e.exit_code)

            except IOError as e:
                if e.errno == errno.EPIPE:
                    sys.stdout = PacifyFlushWrapper(sys.stdout)
                    sys.stderr = PacifyFlushWrapper(sys.stderr)
                    sys.exit(1)
                else: raise
                
        except Exit as e:
            if standalone_mode:
                sys.exit(e.exit_code)
            else:
                # in non-standalone mode, return the exit code
                # note that this is only reached if `self.invoke` above raises
                # an Exit explicitly
                return e.exit_code

        except Abort:
            if not standalone_mode: raise
            echo("Aborted!", file=sys.stderr)
            sys.exit(1)