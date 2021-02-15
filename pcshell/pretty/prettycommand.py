import os
import sys

import click
from click.core import iter_params_for_processing, make_str

from .pretty import PrettyHelper


class PrettyCommand(click.Command):
    def get_help(self, ctx):
        """Formats the help into a string and returns it.
        """
        return PrettyHelper.get_help(self, ctx)

    def format_usage(self, ctx, formatter):
        """Writes the usage line into the formatter.
        """
        PrettyHelper.format_usage(self, ctx, formatter)

    def format_help_text(self, ctx, formatter):
        """Writes the help text to the formatter if it exists."""
        PrettyHelper.format_help_text(self, ctx, formatter)

    def format_options(self, ctx, formatter):
        """Writes all the options into the formatter if they exist."""
        PrettyHelper.format_options(self, ctx, formatter)

    def format_commands(self, ctx, formatter):
        pass

    def format_epilog(self, ctx, formatter):
        """Additional formatting after all of the help text is written"""
        PrettyHelper.format_epilog(self, ctx, formatter)


    def main(self, args=None, prog_name=None, complete_var=None, standalone_mode=True, **extra):
        return PrettyHelper.main(self, args=args, prog_name=prog_name, complete_var=complete_var, standalone_mode=standalone_mode, **extra)


    def parse_args(self, ctx, args):
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()

        print(args)

        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args=args)

        print(opts)
        print(args)

        for param in iter_params_for_processing(param_order, self.get_params(ctx)):
            print(param)
            value, args = param.handle_parse_result(ctx, opts, args)

        if args and not ctx.allow_extra_args and not ctx.resilient_parsing:
            ctx.fail(
                "Got unexpected extra argument{} ({})".format(
                    "s" if len(args) != 1 else "", " ".join(map(make_str, args))
                )
            )

        ctx.args = args
        return args