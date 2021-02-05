import ast
import click


class PrettyOption(click.Option):
    def __init__(self, param_decls, choices=None, **attrs):
        super(PrettyOption, self).__init__(param_decls, **attrs)
        self.choices = choices


    def get_help_record(self, ctx):
        if self.hidden: return None
        return super(PrettyOption, self).get_help_record(ctx)

    
    def type_cast_value(self, ctx, value):
        return super().type_cast_value(ctx, value)


class PythonLiteralOption(PrettyOption):
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except: raise click.BadParameter('Invalid Python Literal Provided: %s' % str(value))