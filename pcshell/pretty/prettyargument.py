from typing import List

import click

from .pretty import PrettyHelper


class PrettyArgument(click.Argument):
    def __init__(self, param_decls, 
        help=None, 
        choices=None, 
        hidden=None, 
        literal=None, 
        literal_tuple_type: List[type] = None, 
    **attrs):
        super(PrettyArgument, self).__init__(param_decls, **attrs)

        self.help = help
        self.hidden = hidden
        self.choices = choices

        self.literal_tuple_type = literal_tuple_type
        self.literal = literal or self.literal_tuple_type


    def get_help_record(self, ctx):
        if self.hidden: return
        help = self.help or ""
        return help


    def handle_parse_result(self, ctx, opts, args):
        return PrettyHelper.handle_parse_result(self, ctx, opts, args)