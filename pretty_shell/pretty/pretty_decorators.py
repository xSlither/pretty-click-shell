import inspect

from click._unicodefun import _check_for_unicode_literals
from click.decorators import _param_memo

from .prettycommand import PrettyCommand
from .prettyargument import PrettyArgument


def argument(*param_decls, **attrs):
    """Attaches an argument to the command.  All positional arguments are
    passed as parameter declarations to :class:`PrettyArgument`; all keyword
    arguments are forwarded unchanged (except ``cls``).
    This is equivalent to creating an :class:`PrettyArgument` instance manually
    and attaching it to the :attr:`Command.params` list.

    :param cls: the argument class to instantiate.  This defaults to
                :class:`PrettyArgument`.
    """

    def decorator(f):
        # Copy attrs, so pre-defined parameters can re-use the same cls=
        arg_attrs = attrs.copy()

        if "help" in arg_attrs:
            arg_attrs["help"] = inspect.cleandoc(arg_attrs["help"])
        ArgumentClass = arg_attrs.pop("cls", PrettyArgument)
        _param_memo(f, ArgumentClass(param_decls, **arg_attrs))
        return f

    return decorator


def prettyCommand(name=None, cls=None, **attrs):
    """Creates a new :class:`PrettyCommand` and uses the decorated function as
    callback.  This will also automatically attach all decorated
    :func:`option`\s and :func:`argument`\s as parameters to the command.

    The name of the command defaults to the name of the function with
    underscores replaced by dashes.  If you want to change that, you can
    pass the intended name as the first argument.

    All keyword arguments are forwarded to the underlying command class.

    Once decorated the function turns into a :class:`PrettyCommand` instance
    that can be invoked as a command line utility or be attached to a
    command :class:`PrettyGroup`.

    :param name: the name of the command.  This defaults to the function
                 name with underscores replaced by dashes.
    :param cls: the command class to instantiate.  This defaults to
                :class:`PrettyCommand`.
    """
    if cls is None:
        cls = PrettyCommand

    def decorator(f):
        cmd = _make_command(f, name, attrs, cls)
        cmd.__doc__ = f.__doc__
        return cmd

    return decorator


def _make_command(f, name, attrs, cls):
    if isinstance(f, PrettyCommand):
        raise TypeError("Attempted to convert a callback into a command twice.")
    try:
        params = f.__click_params__
        params.reverse()
        del f.__click_params__
    except AttributeError:
        params = []
    help = attrs.get("help")
    if help is None:
        help = inspect.getdoc(f)
        if isinstance(help, bytes):
            help = help.decode("utf-8")
    else:
        help = inspect.cleandoc(help)
    attrs["help"] = help
    _check_for_unicode_literals()
    return cls(
        name=name or f.__name__.lower().replace("_", "-"),
        callback=f,
        params=params,
        **attrs
    )