import click


class PrettyOption(click.Option):
    def __init__(self, param_decls, choices=None, **attrs):
        super(PrettyOption, self).__init__(param_decls, **attrs)
        self.choices = choices


    def get_help_record(self, ctx):
        if self.hidden: return None
        return super(PrettyOption, self).get_help_record(ctx)