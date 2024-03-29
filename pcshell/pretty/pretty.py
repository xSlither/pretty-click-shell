from typing import List, Callable, Union

import os
import sys
import re
import json
import shlex
import math

import click
from click.core import (
    Command, Context, Group, MultiCommand, Argument, HelpFormatter, DEPRECATED_HELP_NOTICE,
    PY2, _verify_python3_env, _check_for_unicode_literals, get_os_args, 
    make_str, echo, _bashcomplete, Abort, Exit, ClickException, errno, 
    PacifyFlushWrapper,
    augment_usage_errors, invoke_param_callback,
    iter_params_for_processing,
    split_opt
)
from click.parser import (
    OptionParser, _unpack_args
)

from colorama import Style

from .. import globals as globs
from .. import _colors as colors
from .._utils import HasKey, suggest
from .. import chars



NOCOMMAND = "\n\t{}Command not found: {}%s{}".format(colors.COMMAND_NOT_FOUND_TEXT_STYLE, colors.COMMAND_NOT_FOUND_TEXT_FORE, Style.RESET_ALL)


class PrettyHelper:
    
    @staticmethod
    def get_help(self: Command, ctx: Context):
        """Formats the help into a string and returns it.
        """
        print()
        formatter = ctx.make_formatter()
        self.format_help(ctx, formatter)
        txt = formatter.getvalue().rstrip("\n")
        return '\t' + '\t'.join(txt.splitlines(True))

    @staticmethod
    def format_usage(self: Command, ctx: Context, formatter: HelpFormatter):
        """Writes the usage line into the formatter.
        """
        pieces = self.collect_usage_pieces(ctx)
        formatter.write_usage(ctx.command_path, '{style}{fore}{txt}{reset}'.format(style=colors.HELP_USAGE_STYLE, fore=colors.HELP_USAGE_FORE, txt=" ".join(pieces), reset=Style.RESET_ALL))

    @staticmethod
    def format_help_text(self: Command, ctx: Context, formatter: HelpFormatter):
        """Writes the help text to the formatter if it exists."""
        if self.help:
            formatter.write_paragraph()
            with formatter.indentation():
                help_text = '{fore}{help}{reset}'.format(fore=colors.HELP_TEXT_FORE, help=self.help, reset=Style.RESET_ALL)
                if self.deprecated:
                    help_text += DEPRECATED_HELP_NOTICE
                formatter.write_text(help_text)
                formatter.write_paragraph()
        elif self.deprecated:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(DEPRECATED_HELP_NOTICE)

    @staticmethod
    def format_options(self: Command, ctx: Context, formatter: HelpFormatter):
        """Writes all the arguments & options into the formatter, if they exist."""
        opts = []
        args = []

        for param in self.get_params(ctx):
            help_record = param.get_help_record(ctx)

            if help_record:
                if not isinstance(param, Argument):
                    rv = '{style}{txt}{reset}'.format(style=colors.HELP_OPTION_DESCRIPTION_STYLE, txt=help_record[1], reset=Style.RESET_ALL)
                    if rv is not None:
                        name = '{style}{txt}{reset}'.format(txt='--' + param.name, style=colors.HELP_OPTION_NAME_STYLE, reset=Style.RESET_ALL)
                        opts.append((name, rv))

                else:
                    rv = '{style}{txt}{reset}'.format(style=colors.HELP_ARGUMENT_DESCRIPTION_STYLE, txt=help_record, reset=Style.RESET_ALL)
                    if rv is not None:
                        name = '{style}{txt}{reset}: {class_color}{type}{arrow_color} ->{reset}'.format(
                            txt=param.name, style=colors.HELP_ARGUMENT_NAME_STYLE, reset=Style.RESET_ALL,
                            class_color=colors.HELP_ARGUMENT_CLASS_STYLE, arrow_color=colors.HELP_ARGUMENT_ARROW_STYLE, type=param.type.name
                        )
                        args.append((name, rv))

        if HasKey('aliases', self) and len(self.aliases) > 0:
            with formatter.section('{fore}{back}{style}Aliases{reset}'.format(fore=colors.HELP_ALIASES_HEADER_FORE, back=colors.HELP_ALIASES_HEADER_BACK, style=colors.HELP_ALIASES_HEADER_STYLE, reset=Style.RESET_ALL)):
                formatter.write_dl([('{style}{txt}{reset}'.format(style=colors.HELP_ALIASES_ALIAS_STYLE, txt=', '.join(self.aliases), reset=Style.RESET_ALL), '')])
                formatter.write_paragraph()

        if args:
            with formatter.section('{fore}{back}{style}Arguments{reset}'.format(fore=colors.HELP_ARGUMENT_HEADER_FORE, back=colors.HELP_ARGUMENT_HEADER_BACK, style=colors.HELP_ARGUMENT_HEADER_STYLE, reset=Style.RESET_ALL)):
                formatter.write_dl(args)
                formatter.write_paragraph()

        if opts:
            with formatter.section('{fore}{back}{style}Options{reset}'.format(fore=colors.HELP_OPTION_HEADER_FORE, back=colors.HELP_OPTION_HEADER_BACK, style=colors.HELP_OPTION_HEADER_STYLE, reset=Style.RESET_ALL)):
                formatter.write_dl(opts)

        self.format_commands(ctx, formatter)

    @staticmethod
    def format_commands(self: Command, ctx: Context, formatter: HelpFormatter):
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None: continue
            if cmd.hidden: continue

            commands.append((subcommand, cmd))

        formatter.width += 3
        if len(commands):
            limit = (formatter.width - 6 - max(len(cmd[0]) for cmd in commands))

            rows = []
            for subcommand, cmd in commands:
                help = '{style}{txt}{reset}'.format(txt=cmd.get_short_help_str(limit), style=colors.HELP_COMMAND_DESCRIPTION_STYLE, reset=Style.RESET_ALL)
                rows.append(('{style}{txt}{reset}'.format(txt=subcommand, style=colors.HELP_COMMAND_NAME_STYLE, reset=Style.RESET_ALL), help))

            if rows:
                formatter.write_paragraph()
                with formatter.section('{fore}{back}{style}Commands{reset}'.format(fore=colors.HELP_COMMAND_HEADER_FORE, back=colors.HELP_COMMAND_HEADER_BACK, style=colors.HELP_COMMAND_HEADER_STYLE, reset=Style.RESET_ALL)):
                    formatter.write_dl(rows)

    @staticmethod
    def format_epilog(self: Command, ctx: Context, formatter: HelpFormatter):
        """Additional formatting after all of the help text is written"""
        if self.epilog:
            formatter.write_paragraph()
            for line in self.epilog.split('\n'):
                formatter.write_text(line)


    @staticmethod
    def resolve_command(self: MultiCommand, ctx: Context, args):
        cmd_name = make_str(args[0])
        original_cmd_name = cmd_name

        # Get the command
        cmd = self.get_command(ctx, cmd_name)

        # If we can't find the command but there is a normalization
        # function available, we try with that one.
        if cmd is None and ctx.token_normalize_func is not None:
            cmd_name = ctx.token_normalize_func(cmd_name)
            cmd = self.get_command(ctx, cmd_name)

        # Command not found
        if cmd is None and not ctx.resilient_parsing:
            PrettyHelper.VerifyCommand(self, ctx)
            ctx.abort()

            # if split_opt(cmd_name)[0]:
            #     self.parse_args(ctx, ctx.args)
            # ctx.fail("No such command '{}'.".format(original_cmd_name))
    
        return cmd_name, cmd, args[1:]

    @staticmethod
    def VerifyCommand(self: MultiCommand, ctx: Context):
        line = globs.__CURRENT_LINE__
        commands = []

        for subcommand in self.list_commands(ctx):
            cmd: click.Command = self.get_command(ctx, subcommand)
            if cmd and not cmd.hidden:
                commands.append(cmd.name)
                        
        sug = suggest(commands, line) if len(commands) else None
        click.echo(
            NOCOMMAND % line if not sug else (NOCOMMAND % line) + '.\n\n\t{}{}Did you mean "{}{}{}"?{}'.format(
                colors.SUGGEST_TEXT_STYLE, colors.SUGGEST_TEXT_COLOR, colors.SUGGEST_ITEMS_STYLE, sug, colors.SUGGEST_TEXT_COLOR, Style.RESET_ALL)
        )
        click.echo(chars.IGNORE_LINE)


    @staticmethod
    def StdOut(ret: object) :
        if not globs.__IsShell__:
            try:
                return click.echo((json.dumps(ret, sort_keys=True)).strip())
            except:
                return click.echo(ret.strip())


    @staticmethod
    def main(self: Command, args=None, prog_name=None, complete_var=None, standalone_mode=True, **extra):
        """This is the way to invoke a script with all the bells and
        whistles as a command line application.  This will always terminate
        the application after a call.  If this is not wanted, ``SystemExit``
        needs to be caught.
        """
        # If we are in Python 3, we will verify that the environment is
        # sane at this point or reject further execution to avoid a
        # broken script.
        if not PY2:  _verify_python3_env()
        else: _check_for_unicode_literals()

        if args is None: args = get_os_args()
        else: args = list(args)

        if prog_name is None:
            prog_name = make_str(os.path.basename(sys.argv[0] if sys.argv else __file__))

        # Hook for the Bash completion
        _bashcomplete(self, prog_name, complete_var)

        try:
            try:
                with self.make_context(prog_name, args, **extra) as ctx:
                    rv = self.invoke(ctx)

                    # Send returned data from command to stdout if not in Shell mode, 
                    # automatically dumping the json of serializable objects
                    if rv: PrettyHelper.StdOut(rv)

                    if not standalone_mode:
                        return rv
                    ctx.exit()

            except (EOFError, KeyboardInterrupt):
                echo(file=sys.stderr)
                raise Abort()

            except ClickException as e:
                if not standalone_mode:
                    raise
                e.show()
                sys.exit(e.exit_code)

            except IOError as e:
                if e.errno == errno.EPIPE:
                    sys.stdout = PacifyFlushWrapper(sys.stdout)
                    sys.stderr = PacifyFlushWrapper(sys.stderr)
                    sys.exit(1)
                else: raise
                
        except Exit as e:
            if standalone_mode:
                sys.exit(e.exit_code)
            else:
                # in non-standalone mode, return the exit code
                # note that this is only reached if `self.invoke` above raises
                # an Exit explicitly
                return e.exit_code

        except Abort:
            if not standalone_mode: raise
            echo("Aborted!", file=sys.stderr)
            sys.exit(1)


    @staticmethod
    def handle_parse_result(self, ctx: click.Context, opts, args: List[str], seq: int):
        if not self.literal:
            with augment_usage_errors(ctx, param=self):
                value = self.consume_value(ctx, opts)
                try:
                    value = self.full_process_value(ctx, value)
                except Exception:
                    if not ctx.resilient_parsing:
                        raise
                    value = None
                if self.callback is not None:
                    try:
                        value = invoke_param_callback(self.callback, ctx, self, value)
                    except Exception:
                        if not ctx.resilient_parsing:
                            raise

        elif len(self.literal_tuple_type):
            value = None

            def parse_array(line: str) -> list:
                try:
                    if line.startswith('[') and line.endswith(']'):
                        tmp = line.rstrip()
                        tmp = re.sub(r"((,[\s]*\])|(,[\s]*)|((,\][\s]*)))$", '', tmp)
                        if not tmp.endswith(']'): tmp += ']'
                        return tmp
                except: pass
                
                if line.rstrip().endswith(','): 
                    return '%s]' % line.rstrip()[:-1]
                raise click.BadParameter('Invalid Python Literal Provided: %s' % line)

            def parse_args(args: List[str]) -> str:
                ret = ''
                if len(args):

                    for arg in args:
                        if arg[:-1].replace('.', '', 1).isdigit() or (arg[:-1].lower() == 'true' or arg[:-1].lower() == 'false'):
                            ret += "{}, ".format(arg[:-1])
                        else:
                            if not arg.endswith(']'): ret += '"{}", '.format(arg[:-1])
                            else: 
                                ret += '"{}"'.format(arg[:-1])
                                break

                    return "{}]".format(ret.rstrip())
                return ret

            def parse_value(val: str) -> str:
                if val:
                    val = val[1: -1]
                    if val.replace('.', '', 1).isdigit() or (val.lower() == 'true' or val.lower() == 'false'): return val
                    else: return '"%s"' % val
                else: return None

            def extract_tuple(value: str, args: List[str]) -> list:
                try:
                    if value:
                        if value == '[,': value = '["",'

                        if value[1:-1] == '""' or (value[1:-1].replace('.', '', 1).isdigit() or (value[1:-1].lower() == 'true' or value[1:-1].lower() == 'false')):
                            value = parse_array('{} {}'.format(value, parse_args(args)))
                        else:
                            value = parse_array('["{}", {}'.format(value[1:-1], parse_args(args)))

                        value = json.loads(value)
                        
                    return value
                except Exception as e:
                    raise click.BadParameter('Invalid Python Literal Provided: %s' % str(value))


            #----------------------------------------------------------------------------
            opt_val_count = 0
            with augment_usage_errors(ctx, param=self):
                exists = self.consume_value(ctx, opts)

                def remove_mapitem(dic: dict, key: str, i: int) -> None:
                    dic[key].pop(i)
                    dic['%s_count' % key] -= 1

                def typed_tuple_map() -> dict:
                    line = globs.__CURRENT_LINE__
                    matches = re.findall(r"\s(--[\w]*)([\s]*\[)", line)

                    dic = dict()
                    n = 0
                    
                    for match in matches:
                        if HasKey(match[0], dic):
                            dic[match[0]].append(n)
                            dic['%s_count' % match[0]] += 1
                        else: 
                            dic[match[0]] = [n]
                            dic['%s_count' % match[0]] = 1
                        n += 1
                    return dic

                def split_args(dic: dict) -> List[str]:
                    try:
                        i = dic['--%s' % self.name][dic['--%s_count' % self.name] - 1]
                        ii = 0

                        true_args = []
                        used_args = []
                        
                        for arg in ctx.original_args:
                            if arg.endswith(']'): 
                                if not ii == i: true_args.append(arg)
                                else: used_args.append(arg)
                                ii += 1
                                continue
                        
                            if ii == i: 
                                used_args.append(arg)
                                continue
                            true_args.append(arg)

                        return used_args

                    except IndexError:
                        raise click.ClickException(
                            'Option --{} could not be parsed. Please verify syntax'.format(
                                self.name
                            )
                        ) 


                if exists:

                    tuple_map = typed_tuple_map()

                    if not isinstance(exists, list):
                        # Single Option

                        def format_exists():
                            _val_ = exists[1:-1]

                            if _val_ == '[,': return '""'
                            if _val_.replace('.', '', 1).isdigit():
                                if '.' in _val_: return float(_val_)
                                else: return int(_val_)
                            if _val_.lower() == 'true' or _val_.lower() == 'false': return bool(_val_)
                            return _val_

                        used_args = split_args(tuple_map)
                        value = (extract_tuple(self.name, used_args))

                        value[0] = format_exists()
                        remove_mapitem(tuple_map, ('--%s' % self.name), (tuple_map['--%s_count' % self.name] - 1))
                        opt_val_count += 1

                    else:
                        # Multiple Options
                        value = []

                        for opt in reversed(exists):
                            used_args = split_args(tuple_map)
                            value.append((extract_tuple(opt, used_args)))
                            remove_mapitem(tuple_map, '--%s' % self.name, tuple_map['--%s_count' % self.name] - 1)
                            opt_val_count += 1
                        value.reverse()

                    seq += 1
                    args = None
            #----------------------------------------------------------------------------


        def check_tuple(value):
            if self.literal and self.literal_tuple_type:

                def __check_tuple__(value):
                    valid = False

                    if len(value) == len(self.literal_tuple_type):
                        for i in range(0, len(value)):
                            if not type(value[i]) == self.literal_tuple_type[i]:
                                if str(self.literal_tuple_type[i]).startswith('Choice('): 
                                    if value[i] in self.literal_tuple_type[i].choices: continue
                                    raise click.BadArgumentUsage('"{}" is not a valid argument. Valid choices are: {}'.format(value[i], str(self.literal_tuple_type[i].choices)))
                                
                            else: 
                                valid = True
                                continue

                            valid = False
                            break

                    if not valid:
                        raise click.BadParameter('Tuple type does not match.\n\n\tProvided: {}\n\tExpected: {}'.format(value, self.literal_tuple_type))


                nargs = 0
                total_nargs = 0
                cmd_nargs = 0
                optional_args = 0
                cmd: Command = ctx.command
                
                def get_option(name: str) -> click.Option:
                    for p in cmd.params: 
                        if isinstance(p, click.Option) and p.name == name: return p
                    return None

                for p in ctx.original_params:
                    if p.startswith('--'): 
                        option = get_option(p[2:])
                        if option and not (option.is_bool_flag or option.is_flag):
                            break
                        else: continue
                    nargs += 1

                for a in cmd.params:
                    if isinstance(a, click.Argument):
                        if a.required:
                            cmd_nargs += 1
                            if HasKey('nargs', a): cmd_nargs += a.nargs - 1
                        else:
                            optional_args += 1

                        total_nargs += 1
                        if HasKey('nargs', a): total_nargs += a.nargs - 1


                if nargs < cmd_nargs:
                    raise click.ClickException(
                        'Required Arguments are missing. Provided {} argument(s); expected {} (minimum)'.format(
                            nargs, cmd_nargs
                        )
                    )

                elif nargs > total_nargs:
                    raise click.ClickException(
                        'Too many Arguments. Provided {} argument(s); expected {} (maximum)'.format(
                            nargs, total_nargs
                        )
                    ) 
                        

                if len(value) and isinstance(value[0], list):
                    # Multiple Option
                    for v in value: __check_tuple__(v)
                else: 
                    # Single Option
                    __check_tuple__(value)


        #----------------------------------------------------------------------------
        if value: check_tuple(value)

        if self.expose_value:
            ctx.params[self.name] = value

        return value, args, seq
        #----------------------------------------------------------------------------


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
                try:
                    n = check_tuple((i + k) + 1)
                    if n > 0:
                        ret.append(parsed_line[v])
                        i += n + 1
                        continue
                except: pass

            ret.insert(k + kk, parsed_line[v])
            kk += 1
            i += 1
        return ret

    @staticmethod
    def parse_args(self: Command, ctx: Context, args: List[str], supportsLiterals: Callable[[click.Parameter], bool]):
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()

        args = PrettyHelper.parse_line(args)
        ctx.original_params = args.copy()

        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args=args)
        ctx.original_args = args.copy()

        i = 0
        for param in iter_params_for_processing(param_order, self.get_params(ctx)):
            if supportsLiterals(param):
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


class PrettyParser(OptionParser):

    def __anlayzeTuples(self, option: click.Option, value: str, cmd_nargs: int, args) -> int:

        from .._completion import COMPLETION_TREE, deep_get

        true_line = globs.__CURRENT_LINE__.rstrip()
        line = (((' '.join(globs.__SHELL_PATH__) + ' ') if len(globs.__SHELL_PATH__) else '') + true_line).rstrip()

        if ' ' in line: words = line.split(' ')
        else: words = [line]

        if ' ' in true_line: original_words = true_line.rstrip().split(' ')
        else: original_words = [true_line]

        priorOption = words[len(words) - 3] if len(words) > 2 else None

        current_key = []
        for i in range(0, len(words)):
            if i < len(globs.__SHELL_PATH__): continue

            try:
                if deep_get(COMPLETION_TREE, *words[:len(words) - i]):
                    if len(original_words) > 2: 
                        current_key = words[:(len(words) - (i - 1)) + len(globs.__SHELL_PATH__)]
                    elif '--' in words: current_key = words[:len(words) - i] 
                    else:
                        current_key = words[:len(words) - (i - 1)]
                        if deep_get(COMPLETION_TREE, *current_key): break

                elif priorOption and '--' in priorOption:
                    current_key = words[:len(words) - (i + 1)]
                    if deep_get(COMPLETION_TREE, *current_key):  break

                else:
                    key = words[:len(words) - (i + 1)]
                    if deep_get(COMPLETION_TREE, *key):
                        current_key = key
                        break
            except Exception as e: break

        obj = deep_get(COMPLETION_TREE, *current_key)
        obj2 = deep_get(COMPLETION_TREE, *words)


        def get_option(name: str) -> click.Option:
            if len(obj['_options']):
                try: return [x for x in obj['_options'] if x[0] == name][0][1]
                except IndexError: pass
            return None

        def get_option_names() -> List[str]:
            expression = r'(?<=--)([a-zA-Z0-9]*)(?=\s)'
            return re.findall(expression, line)

        def AnalyzeOptions():
            option_names = get_option_names()
            ret = 0
            for oName in option_names:
                option = get_option('--%s' % oName)
                if option:
                    if not (option.is_bool_flag or option.is_flag): 
                        ret += 2
                        if HasKey('nargs', option) and option.nargs > 1:
                            ret += (option.nargs - 1)
                    else: ret += 1
            return ret


        def AnalyzeArgs():
            ret = 0
            if len(obj['_arguments']):
                for arg in obj['_arguments']:
                    _arg: PrettyArgument = arg[1]
                    if _arg and HasKey('nargs', _arg) and _arg.nargs > 1:
                        ret += (_arg.nargs - 1)
            return ret

        def check_literal():
            def check_tuple(i: int) -> int:
                n = 0
                try:
                    if original_words[i].startswith('['):
                        for item in original_words[i:]:
                            n += 1
                            if item.endswith(']'): break
                except IndexError: return 0
                return n

            ret = 0
            ii = 0
            for w in range(0, len(original_words)):
                if ii > w: continue

                if original_words[w].startswith('--'):
                    n = check_tuple(ii + 1)
                    if n > 0:
                        ret += n - 1
                        ii += n + 1
                        continue
                ii += 1
            return ret

        def getNargMap():
            i = 0
            ret = []
            if len(obj['_arguments']):
                for arg in obj['_arguments']:
                    _arg: PrettyArgument = arg[1]
                    if _arg and HasKey('nargs', _arg):
                        for n in range(0, _arg.nargs):
                            ret.append(i)
                    else: ret.append(i)
                    i += 1
            return ret

        def getNargCountMap():
            ret = []
            if len(obj['_arguments']):
                for arg in obj['_arguments']:
                    _arg: PrettyArgument = arg[1]
                    if _arg and HasKey('nargs', _arg):
                        i = 0
                        for n in range(0, _arg.nargs):
                            ret.append(i)
                            i += 1
                    else: ret.append(0)
            return ret


        words_len = len(words) - len(current_key)
        words_len -= check_literal()

        nargs = words_len
        nargs -= AnalyzeOptions()
        nargs_count = nargs - AnalyzeArgs()
        narg_map = getNargMap()
        narg_count_map = getNargCountMap()

        flag_valid_comma_arg = False
        if len(obj['_arguments']):
            if nargs_count - 1 < len(obj['_arguments']):
                arg_index = nargs - 1 if nargs > 0 else 0
                arg = obj['_arguments'][narg_map[arg_index]]

                flag_valid_comma_arg = arg and (nargs == arg_index)


        query = '(?<=--{name}\s)(\[.*?\])'.format(name=option.name)
        match = re.search(query, line)

        from .._lexer import ShellLexer # Import here to prevent circular reference. Need to refactor code to separte module
        from pygments.token import Name
        lexer = ShellLexer()
        tokens = lexer.get_tokens(line)

        invalid = False
        for token in tokens:
            if token[0] == Name.InvalidCommand:
                invalid = True
                break

        json_string = '[%s]' % match[0]
        if json_string[1] == '[': json_string = json_string[1:]
        if json_string[-1] == ']': json_string = json_string[:-1]

        try:
            tuple_values = json.loads(json_string)
        except: return 1

        if tuple_values and len(option.literal_tuple_type) == len(tuple_values):
            if invalid: 
                if nargs > cmd_nargs: return -1
                else: return -2
            else: 
                if not flag_valid_comma_arg: 
                    if ']' in value and json_string.endswith(value):
                        return 0
                    elif value.endswith(',') and (' %s ' % value) in json_string:
                        return 0
                    return -1
                else: return 0
        else: return 1


    def _process_args_for_args(self, state):
        pargs, args = _unpack_args(
            state.largs + state.rargs, [x.nargs for x in self._args]
        )

        total_nargs = 0
        cmd_nargs = 0
        optional_args = 0


        def get_tuple_insert_index(option, value):
            true_line = globs.__CURRENT_LINE__.rstrip()
            line = (((' '.join(globs.__SHELL_PATH__) + ' ') if len(globs.__SHELL_PATH__) else '') + true_line).rstrip()

            query = '(?<=--{name}\s)(\[.*?\])'.format(name=option.name)
            match = re.search(query, line)

            json_string = '[%s]' % match[0]
            if json_string[1] == '[': json_string = json_string[1:]
            if json_string[-1] == ']': json_string = json_string[:-1]

            try:
                tuple_values = json.loads(json_string)
            except: return 0

            i = 0
            for item in tuple_values:
                try:
                    if str(value[:-1]) == str(item): break
                except: pass
                
                try:
                    if int(value[:-1]) == item: break
                except: pass

                try:
                    if float(value[:-1]) == item: break
                except: pass

                try:
                    b = str(item).lower()
                    if b == 'true' or b == 'false':
                        if str(item).lower() == value[:-1].lower(): break 
                except: pass

                i += 1

            if i <= (len(tuple_values) / 2):
                return round(i / 2)
            else: return math.ceil(i / 2)


        for idx, arg in enumerate(self._args):
            if arg.obj.required:
                cmd_nargs += 1
                if HasKey('nargs', arg.obj): cmd_nargs += arg.obj.nargs - 1
            else: optional_args += 1

            total_nargs += 1
            if HasKey('nargs', arg.obj): total_nargs += arg.obj.nargs - 1

        used_optional_narg = 0
        for idx, arg in enumerate(self._args):
            if not arg.obj.required:

                if used_optional_narg < optional_args:
                    if (pargs[idx] and len(pargs[idx])) and (pargs[idx][-1] == ',' or pargs[idx][-1] == ']'):
                        try: prev_option = state.order[used_optional_narg]
                        except: pass

                        if prev_option and prev_option.literal_tuple_type:

                            analyze_result = self.__anlayzeTuples(prev_option, pargs[idx], total_nargs, args)

                            if analyze_result == 0:
                                
                                args.insert(get_tuple_insert_index(prev_option, pargs[idx]), pargs[idx])
                                # used_optional_narg += 1

                            else:
                                if analyze_result < 0: 
                                    arg.process(pargs[idx], state)
                                    if analyze_result < -1:
                                        args.pop(0)
                                elif analyze_result > 0:
                                    args.pop(0)
                                    used_optional_narg += 1

                        else: arg.process(pargs[idx], state)
                    else: arg.process(pargs[idx], state)
                else: arg.process(pargs[idx], state)
            else: arg.process(pargs[idx], state)

        state.largs = args
        state.rargs = []