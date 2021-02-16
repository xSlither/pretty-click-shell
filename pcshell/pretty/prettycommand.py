from typing import List

import os
import sys
import re

import click
from click.core import iter_params_for_processing, make_str

from .pretty import PrettyHelper
from .prettyoption import PrettyOption


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


    @staticmethod
    def parse_line(line: List[str]) -> List[str]:
        def check_tuple(i: int) -> int:
            n = 0
            if line[i].startswith('['):
                for item in line[i:]:
                    n += 1
                    if item.endswith(']'): break
            return n
            
        def get_first_opt() -> int:
            n = 0
            for item in line:
                match = re.match(r'^--[/w]*', item)
                if match: return n
                n += 1
            return n
        
        ret: List[str] = []
        k = get_first_opt()

        for i in range(0, len(line)):
            if i == k: break
            ret.append(line[i])

        i = 0
        kk = 0
        parsed_line = line[k:]
        for v in range(0, len(parsed_line)):
            if i > v:
                ret.append(parsed_line[v])
                continue

            if parsed_line[v].startswith('--'):
                n = check_tuple((i + k) + 1)
                if n > 0:
                    ret.append(parsed_line[v])
                    i += n + 1
                    continue

            ret.insert(k + kk, parsed_line[v])
            kk += 1
            i += 1
        return ret

    def parse_args(self, ctx, args):
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()

        args = PrettyCommand.parse_line(args)

        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args=args)

        i = 0
        for param in iter_params_for_processing(param_order, self.get_params(ctx)):
            if isinstance(param, PrettyOption):
                value, args, i = param.handle_parse_result(ctx, opts, args, i)
            else:
                value, args = param.handle_parse_result(ctx, opts, args)

        if args and not ctx.allow_extra_args and not ctx.resilient_parsing:
            ctx.fail(
                "Got unexpected extra argument{} ({})".format(
                    "s" if len(args) != 1 else "", " ".join(map(make_str, args))
                )
            )

        ctx.args = args
        return args