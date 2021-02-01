import click


class PrettyArgument(click.Argument):
    def __init__(self, param_decls, help=None, choices=None, hidden=None, **attrs):
        super(PrettyArgument, self).__init__(param_decls, **attrs)

        self.help = help
        self.hidden = hidden
        self.choices = choices


    def get_help_record(self, ctx):
        if self.hidden: return
        help = self.help or ""
        return help