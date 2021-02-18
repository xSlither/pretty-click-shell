import click

from .pretty import PrettyHelper
from .prettyoption import PrettyOption


class PrettyGroup(click.Group):
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
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        PrettyHelper.format_commands(self, ctx, formatter)

    def format_epilog(self, ctx, formatter):
        """Additional formatting after all of the help text is written"""
        PrettyHelper.format_epilog(self, ctx, formatter)


    def resolve_command(self, ctx, args):
        return PrettyHelper.resolve_command(self, ctx, args)


    def add_command(self, cmd, name=None):
        name = name or cmd.name
        if name is None:
            raise TypeError("Command has no name.")

        if type(name) is str:
            self.commands[name] = cmd
        else:
            for _name_ in name:
                self.commands[_name_] = cmd

    def command(self, *args, **kwargs):
        """A shortcut decorator for declaring and attaching a command to
        the group.  This takes the same arguments as :func:`command` but
        immediately registers the created command with this instance by
        calling into :meth:`add_command`.
        """
        from .pretty_decorators import prettyCommand

        def decorator(f):
            cmd = prettyCommand(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator


    def group(self, *args, **kwargs):
        """A shortcut decorator for declaring and attaching a group to
        the group.  This takes the same arguments as :func:`group` but
        immediately registers the created command with this instance by
        calling into :meth:`add_command`.
        """
        from .pretty_decorators import prettyGroup

        def decorator(f):
            cmd = prettyGroup(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator


    def main(self, args=None, prog_name=None, complete_var=None, standalone_mode=True, **extra):
        return PrettyHelper.main(self, args=args, prog_name=prog_name, complete_var=complete_var, standalone_mode=standalone_mode, **extra)


    def parse_args(self, ctx, args):
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()

        args = PrettyHelper.parse_line(args)

        rest = click.Command.parse_args(self, ctx, args)
        if self.chain:
            ctx.protected_args = rest
            ctx.args = []
        elif rest:
            ctx.protected_args, ctx.args = rest[:1], rest[1:]

        return ctx.args