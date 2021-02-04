from typing import List, Union
from functools import reduce
import re

import click

from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.completion import (
    Completer, FuzzyCompleter, Completion
)

from .pretty import PrettyArgument
from .utils import HasKey

from . import globals as globs
from . import _colors as colors


COMPLETION_TREE = {}


def deep_get(dictionary, *keys):
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)

def deep_set(dictionary, value, *keys):
    for key in keys[:-1]: dictionary = dictionary[key]
    dictionary[keys[-1]] = value


def html_escape(s: str):
    return s.translate(str.maketrans(
        {
            "&": r"&#38;",
            "<": r"&#60;",
            ">": r"&#62;",
            "\"": r"&#34;",
            "'": r"&#39;",
        }
    ))


class ClickCompleter(Completer):
    def get_completions(self, document, complete_event):
        word: str = document.get_word_before_cursor()
        line: str = document.current_line_before_cursor

        line = ((' '.join(globs.__SHELL_PATH__) + ' ') if len(globs.__SHELL_PATH__) else '') + line

        words = line.rstrip().split(' ')
        lastword = words[len(words) - 1]
        priorOption = words[len(words) - 2] if len(words) > 1 else None

        try:
            current_key = []
            for i in range(0, len(words)):
                if deep_get(COMPLETION_TREE, *words[:len(words) - i]):
                    if len(words) > 2: current_key = words[:len(words) - (i - 1)]
                    elif '--' in lastword: current_key = words[:len(words) - i]
                    else: 
                        current_key = words[:len(words) - (i - 1)]
                        if deep_get(COMPLETION_TREE, *current_key): break

                elif priorOption and '--' in priorOption:
                    current_key = words[:len(words) - (i + 1)]
                    if deep_get(COMPLETION_TREE, *current_key): break

                else:
                    if deep_get(COMPLETION_TREE, *words[:len(words) - (i + 1)]):
                        current_key = words[:len(words) - (i + 1)]
                        break

            obj = deep_get(COMPLETION_TREE, *current_key)
            obj2 = deep_get(COMPLETION_TREE, *words)

            l = len(words)
            c = len([x for x in words if '--' in x])
            l -= c if c else 0


            # Recommend Commands
        
            if obj:
                if obj2 and obj2['isGroup']:
                    commands = [k for k, v in obj2.items() if isinstance(obj2[k], dict)]
                    for key in commands:
                        if key.startswith(word):
                            h = html_escape(obj2[key]['_help'])
                            if not current_key == globs.__SHELL_PATH__:
                                yield Completion(
                                    key,
                                    start_position=-len(word),
                                    display=HTML("<%s>%s</%s>" % (colors.COMPLETION_COMMAND_NAME, key, colors.COMPLETION_COMMAND_NAME)),
                                    display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_COMMAND_DESCRIPTION, h))
                                )
                            else:
                                yield Completion(
                                    key,
                                    start_position=-len(word),
                                    display=HTML("<%s>%s</%s>" % (colors.COMPLETION_ROOT_COMMAND_NAME, key, colors.COMPLETION_ROOT_COMMAND_NAME)),
                                    display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_ROOT_COMMAND_DESCRIPTION, h))
                                )

                elif obj['isGroup'] and not obj2:
                    root = deep_get(COMPLETION_TREE, words[0 + (l - 1)])
                    if root or line.count(' ') == 0:
                        if (root and line.count(' ') == 0) or not root:
                            commands = [k for k, v in obj.items() if isinstance(obj[k], dict)]
                            for key in commands:
                                if key.startswith(word):
                                    h = html_escape(obj[key]['_help'])
                                    yield Completion(
                                        key,
                                        start_position=-len(word),
                                        display=HTML("<%s>%s</%s>" % (colors.COMPLETION_ROOT_COMMAND_NAME, key, colors.COMPLETION_ROOT_COMMAND_NAME)),
                                        display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_ROOT_COMMAND_DESCRIPTION, h))
                                    )


                if len(current_key):

                    def get_option(name: str):
                        if len(obj['_options']):
                            try: return [x for x in obj['_options'] if x[0] == name][0][1]
                            except IndexError: pass
                        return None

                    def get_option_names():
                        expression = r'(?<=--)([a-zA-Z0-9]*)(?=\s)'
                        return re.findall(expression, line)

                    def get_option_display_tag(option, value, isChoice=False, isBool=False):
                        tag = colors.COMPLETION_CHOICE_DEFAULT

                        if isChoice:
                            try:
                                if len(option.choices.display_tags):
                                    tag = option.choices.display_tags[values.index(value)]
                            except: pass
                                
                            try:
                                if len(option.type.display_tags):
                                    tag = option.type.display_tags[values.index(value)]
                            except: pass

                        if isBool:
                            tag = colors.COMPLETION_CHOICE_BOOLEAN_TRUE if value == 'true' else colors.COMPLETION_CHOICE_BOOLEAN_FALSE

                        return tag


                    # Recommend Option Choices

                    if len(obj['_options']):
                        option = get_option(lastword)
                        if option:
                            if not (option.is_bool_flag or option.is_flag):
                                values = []

                                isChoice = False
                                isBool = False

                                if option.type.name == 'choice':
                                    isChoice = True
                                    values = [c for c in option.type.choices if c]
                                elif option.choices and ('Choice' in str(type(option.choices))): 
                                    isChoice = True
                                    values = [c for c in option.choices.choices if c]
                                elif option.type.name == 'boolean': 
                                    isBool = True
                                    values = ['true', 'false']

                                for value in values:
                                    if value.startswith(word):
                                        tag = get_option_display_tag(option, value, isChoice=isChoice, isBool=isBool)

                                        yield Completion(
                                            value,
                                            start_position=-len(word),
                                            display=HTML("<{}>{}</{}>".format(
                                                tag,
                                                value,
                                                tag
                                            ))
                                        )
                                return


                    # Recommend Options

                    if len(obj['_options']):
                        for opt in obj['_options']:
                            name = opt[0]
                            option: click.Option = opt[1]

                            if name == '--help' or name == '-h': continue
                            if option.hidden: continue

                            if (not name in line) or option.multiple:
                                if name.startswith(word):
                                    h = html_escape(option.help) if option.help else ''
                                    yield Completion(
                                        name,
                                        start_position=-len(word),
                                        display=HTML("<%s>%s</%s>" % (colors.COMPLETION_OPTION_NAME, name, colors.COMPLETION_OPTION_NAME)),
                                        display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_OPTION_DESCRIPTION, h))
                                    )

                    # Recommend Arguments

                    if len(obj['_arguments']):
                        nargs = len(words) - len(current_key)

                        def AnalyzeOptions():
                            option_names = get_option_names()
                            ret = 0
                            for oName in option_names:
                                option = get_option('--%s' % oName)
                                if option:
                                    if not (option.is_bool_flag or option.is_flag): ret += 2
                            return ret

                        nargs = nargs - AnalyzeOptions()
                        if nargs < len(obj['_arguments']):
                            arg = obj['_arguments'][nargs - 1 if nargs > 0 else 0]

                            name = arg[0]
                            argument: PrettyArgument = arg[1]
                            values = arg[2]

                            h = html_escape(argument.help) if argument.help else ''

                            isChoice = bool(argument.type.name == 'choice' or argument.choices)
                            isBool = argument.type.name == 'boolean'

                            if isChoice or isBool:
                                for choice in values:
                                    if not choice: continue
                                    if choice.startswith(word):
                                        tag = get_option_display_tag(argument, choice, isChoice=isChoice, isBool=isBool)
                                        yield Completion(
                                            choice,
                                            start_position=-len(word),
                                            display=HTML("<{}>{}</{}>".format(
                                                tag,
                                                choice,
                                                tag
                                            ))
                                        )
                            else:
                                yield Completion(
                                    ' ',
                                    start_position=-1,
                                    display=HTML("<%s>%s</%s>" % (colors.COMPLETION_ARGUMENT_NAME, name, colors.COMPLETION_ARGUMENT_NAME)),
                                    display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_ARGUMENT_DESCRIPTION, h))
                                )

        except Exception: return


class StyledFuzzyCompleter(FuzzyCompleter):
    def _get_display(self, fuzzy_match, word_before_cursor):
        """
        Generate formatted text for the display label.
        """
        m = fuzzy_match
        word = m.completion.text
        disp = m.completion.display

        if m.match_length == 0:
            # No highlighting when we have zero length matches (no input text).
            return disp

        result = []

        # Text before match
        result.append((disp[0][0], word[:m.start_pos]))

        # The match itself
        characters = list(word_before_cursor)

        for c in word[m.start_pos:m.start_pos + m.match_length]:
            classname = 'class:underline.bold'
            if characters and c.lower() == characters[0].lower():
                classname += '.character'
                del characters[0]

            result.append((classname, c))

        # Text after match
        result.append(
            (disp[0][0], word[m.start_pos + m.match_length:]))

        return result


def get_completer(fuzzy=True):
    return StyledFuzzyCompleter(ClickCompleter()) if fuzzy else ClickCompleter()


def BuildCompletionTree(ctx: click.Context):
    global COMPLETION_TREE

    # Extract Groups
    def get_subcommands(ctx: click.Context):
        if isinstance(ctx, click.Context): command = ctx.command
        else: command: click.Command = ctx
            
        commands = []
        try:
            for subcommand in command.list_commands(ctx):
                cmd: click.Command = command.get_command(ctx, subcommand)
                if cmd is None: continue
                if cmd.hidden: continue

                commands.append((subcommand, cmd))
        except Exception as e: pass
        return commands

    # Extract Options / Arguments
    def get_params(ctx: Union[click.Context, click.Command], arguments=False):
        command = ctx.command if isinstance(ctx, click.Context) else ctx
        ret = []

        def get_arg_values(param):
            if param.type.name == 'choice' or (param.choices and 'Choice' in str(type(param.choices))): 
                return param.type.choices if param.type.name == 'choice' else param.choices.choices

            elif param.type.name == 'integer range' or param.type.name == 'float range': 
                return [str(param.type.min), str(param.type.max)]

            elif param.type.name == 'boolean': 
                return ['true', 'false']

            return []

        for param in command.get_params(ctx):
            try:
                if not arguments:
                    if isinstance(param, click.Option):
                        option: click.Option = param
                        name = '--{}'.format(option.name)
                        ret.append((name, option))

                else:
                    if isinstance(param, click.Argument):
                        name = '({txt}: {type})'.format(txt=param.name, type=param.type.name)
                        values = get_arg_values(param)
                        ret.append((name, param, values))
            except: continue
        return ret

    # Recursive function to build completion dictionary
    def build_tree(ctx: Union[click.Context, click.Command], parents: List[str], root=False):
        cmd: click.Command = ctx.command if isinstance(ctx, click.Context) else ctx

        commands = get_subcommands(ctx)
        args = get_params(ctx, True)
        opts = get_params(ctx)

        if not parents: parents = []
        if len(commands):
            for command in commands:
                if not root and isinstance(cmd, click.Group): parents.append(cmd.name)
                build_tree(command[1], parents)
                if len(parents): parents.pop()

        if len(parents):
            if not deep_get(COMPLETION_TREE, *parents):
                deep_set(COMPLETION_TREE, { 
                    "isGroup": True, 
                    "isRoot": False,
                    "CommandTree": parents
                }, *parents)

        keys = parents.copy()
        if not isinstance(cmd, click.Group):
            keys.append(cmd.name)
            deep_set(COMPLETION_TREE, {
                "isGroup": False,
                "CommandTree": parents,
                "isShell": False,
                "isRoot": False,
                "_options": opts,
                "_arguments": args,
                "_help": cmd.short_help or cmd.help
            }, *keys)

        elif not root:
            from .shell import Shell
            keys.append(cmd.name)
            dic = deep_get(COMPLETION_TREE, *keys)
            dic['isShell'] = bool(isinstance(cmd, Shell) and cmd.isShell)
            dic['_options'] = opts
            dic['_arguments'] = args
            dic['_help'] = cmd.short_help or cmd.help

        elif root:
            COMPLETION_TREE['isGroup'] = True
            COMPLETION_TREE['CommandTree'] = []
            COMPLETION_TREE['isShell'] = True
            COMPLETION_TREE['isRoot'] = True

            COMPLETION_TREE['_options'] = opts
            COMPLETION_TREE['_arguments'] = args
            COMPLETION_TREE['_help'] = cmd.short_help or cmd.help

    build_tree(ctx, [], root=True)
    # print(COMPLETION_TREE)