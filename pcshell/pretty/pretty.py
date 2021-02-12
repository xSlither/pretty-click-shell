from typing import List

import os
import sys
import json

import click
from click.core import (
    Command, Context, Argument, HelpFormatter, DEPRECATED_HELP_NOTICE,
    PY2, _verify_python3_env, _check_for_unicode_literals, get_os_args, 
    make_str, echo, _bashcomplete, Abort, Exit, ClickException, errno, 
    PacifyFlushWrapper,
    augment_usage_errors, invoke_param_callback
)

from colorama import Style

from .. import globals as globs
from .. import _colors as colors


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
        formatter.write_usage(ctx.command_path, '{style}{fore}{txt}{reset}'.format(style=colors.HELP_USAGE_STYLE, fore=colors.HELP_USAGE_FORE, txt=" ".join(pieces), reset=Style.RESET_ALL))

    @staticmethod
    def format_help_text(self: Command, ctx: Context, formatter: HelpFormatter):
        """Writes the help text to the formatter if it exists."""
        if self.help:
            formatter.write_paragraph()
            with formatter.indentation():
                help_text = '{fore}{help}{reset}'.format(fore=colors.HELP_TEXT_FORE, help=self.help, reset=Style.RESET_ALL)
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
                    rv = '{style}{txt}{reset}'.format(style=colors.HELP_OPTION_DESCRIPTION_STYLE, txt=help_record[1], reset=Style.RESET_ALL)
                    if rv is not None:
                        name = '{style}{txt}{reset}'.format(txt='--' + param.name, style=colors.HELP_OPTION_NAME_STYLE, reset=Style.RESET_ALL)
                        opts.append((name, rv))

                else:
                    rv = '{style}{txt}{reset}'.format(style=colors.HELP_ARGUMENT_DESCRIPTION_STYLE, txt=help_record, reset=Style.RESET_ALL)
                    if rv is not None:
                        name = '{style}{txt}{reset}: {class_color}{type}{arrow_color} ->{reset}'.format(
                            txt=param.name, style=colors.HELP_ARGUMENT_NAME_STYLE, reset=Style.RESET_ALL,
                            class_color=colors.HELP_ARGUMENT_CLASS_STYLE, arrow_color=colors.HELP_ARGUMENT_ARROW_STYLE, type=param.type.name
                        )
                        args.append((name, rv))

        if args:
            with formatter.section('{fore}{back}{style}Arguments{reset}'.format(fore=colors.HELP_ARGUMENT_HEADER_FORE, back=colors.HELP_ARGUMENT_HEADER_BACK, style=colors.HELP_ARGUMENT_HEADER_STYLE, reset=Style.RESET_ALL)):
                formatter.write_dl(args)
                formatter.write_paragraph()

        if opts:
            with formatter.section('{fore}{back}{style}Options{reset}'.format(fore=colors.HELP_OPTION_HEADER_FORE, back=colors.HELP_OPTION_HEADER_BACK, style=colors.HELP_OPTION_HEADER_STYLE, reset=Style.RESET_ALL)):
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
                help = '{style}{txt}{reset}'.format(txt=cmd.get_short_help_str(limit), style=colors.HELP_COMMAND_DESCRIPTION_STYLE, reset=Style.RESET_ALL)
                rows.append(('{style}{txt}{reset}'.format(txt=subcommand, style=colors.HELP_COMMAND_NAME_STYLE, reset=Style.RESET_ALL), help))

            if rows:
                formatter.write_paragraph()
                with formatter.section('{fore}{back}{style}Commands{reset}'.format(fore=colors.HELP_COMMAND_HEADER_FORE, back=colors.HELP_COMMAND_HEADER_BACK, style=colors.HELP_COMMAND_HEADER_STYLE, reset=Style.RESET_ALL)):
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


    @staticmethod
    def handle_parse_result(self, ctx, opts, args):
        if not self.literal:
            with augment_usage_errors(ctx, param=self):
                value = self.consume_value(ctx, opts)
                try:
                    value = self.full_process_value(ctx, value)
                except Exception:
                    if not ctx.resilient_parsing:
                        raise
                    value = None
                if self.callback is not None:
                    try:
                        value = invoke_param_callback(self.callback, ctx, self, value)
                    except Exception:
                        if not ctx.resilient_parsing:
                            raise

        elif len(self.literal_tuple_type):

            def parse_array(line: str) -> list:
                try:
                    if line.startswith('[') and line.endswith(']'):
                        return line
                except: pass
                
                if line.rstrip().endswith(','): 
                    return '%s]' % line.rstrip()[:-1]
                raise click.BadParameter('Invalid Python Literal Provided: %s' % str(value))

            def parse_args() -> str:
                ret = ''
                if len(args):
                    for arg in args:
                        if arg[:-1].replace('.', '', 1).isdigit() or (arg[:-1].lower() == 'true' or arg[:-1].lower() == 'false'):
                            ret += "{}, ".format(arg[:-1])
                        else:
                            ret += '"{}", '.format(arg[:-1])
                    return "{}]".format(ret.rstrip()[:-1])
                return ret

            def parse_value(val: str) -> str:
                val = val[1: -1]
                if val.replace('.', '', 1).isdigit() or (val.lower() == 'true' or val.lower() == 'false'): return val
                else: return '"%s"' % val


            with augment_usage_errors(ctx, param=self):
                try:
                    value = parse_value(self.consume_value(ctx, opts))
                    value = parse_array('[{}, {}'.format(value, parse_args()))
                    value = json.loads(value)

                    args = None
                except Exception as e:
                    raise click.BadParameter('Invalid Python Literal Provided: %s' % str(value))


        def check_tuple():
            valid = False
            if self.literal and self.literal_tuple_type:
                if len(value) == len(self.literal_tuple_type):
                    for i in range(0, len(value)):
                        if not type(value[i]) == self.literal_tuple_type[i]:
                            if str(self.literal_tuple_type[i]).startswith('Choice('): 
                                if value[i] in self.literal_tuple_type[i].choices: continue
                                raise click.BadArgumentUsage('"{}" is not a valid argument. Valid choices are: {}'.format(value[i], str(self.literal_tuple_type[i].choices)))
                            
                        else: 
                            valid = True
                            continue

                        valid = False
                        break

                if not valid: raise click.BadParameter('Tuple type does not match.\n\n\tProvided: {}\n\tExpected: {}'.format(value, self.literal_tuple_type))


        check_tuple()
        if self.expose_value:
            ctx.params[self.name] = value

        return value, args