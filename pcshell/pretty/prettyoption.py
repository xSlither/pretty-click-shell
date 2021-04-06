from typing import List

import click

from .pretty import PrettyHelper


class PrettyOption(click.Option):
    def __init__(self, param_decls, 
        choices=None, 
        literal=None, 
        literal_tuple_type: List[type] = None, 
    **attrs):
        super(PrettyOption, self).__init__(param_decls, **attrs)
        self.choices = choices

        self.literal_tuple_type = literal_tuple_type
        self.literal = literal or self.literal_tuple_type


    def get_help_record(self, ctx):
        if self.hidden: return None
        return super(PrettyOption, self).get_help_record(ctx)


    def handle_parse_result(self, ctx, opts, args, seq=None):
        if isinstance(seq, int):
            return PrettyHelper.handle_parse_result(self, ctx, opts, args, seq)
        else: return super(PrettyOption, self).handle_parse_result(ctx, opts, args)