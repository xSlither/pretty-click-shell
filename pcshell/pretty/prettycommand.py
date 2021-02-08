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