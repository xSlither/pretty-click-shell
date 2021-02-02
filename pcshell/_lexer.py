import click
import re

from pygments.lexer import RegexLexer, bygroups
from pygments.token import (
    Punctuation,
    Text,
    Operator,
    Keyword,
    Name,
    String,
    Number,
    Generic,
    Comment
)

from ._completion import COMPLETION_TREE, deep_get


def command_lexer(lexer, match):
    line = ''.join(match.groups())
    words = line.split(' ')
    words.pop()

    priorOption = words[len(words) - 2] if len(words) > 1 else None

    command_token = Name.InvalidCommand
    subcommand_token = Name.InvalidCommand

    current_key = []
    for i in range(0, len(words)):
        if deep_get(COMPLETION_TREE, *words[:len(words) - i]):
            if len(words) > 2: current_key = words[:len(words) - (i - 1)]
            elif '--' in words: current_key = words[:len(words) - i]
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
    c = len([x for x in commands if '--' in x])
    l -= c if c else 0

    

    if obj:
        if obj2 and obj2['isGroup']:
            commands = [k for k, v in obj2.items() if isinstance(obj2[k], dict)]
            for key in commands:
                if key.startswith(word):
                    h = html_escape(obj2[key]['help'])
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
                            h = html_escape(obj[key]['help'])
                            yield Completion(
                                key,
                                start_position=-len(word),
                                display=HTML("<%s>%s</%s>" % (colors.COMPLETION_ROOT_COMMAND_NAME, key, colors.COMPLETION_ROOT_COMMAND_NAME)),
                                display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_ROOT_COMMAND_DESCRIPTION, h))
                            )



def command_callback(lexer, match):

    def find_command(keys):
        cmd = deep_get(COMPLETION_TREE, *keys)
        return cmd if cmd else None

    command = match.group(1)
    has_subcommand = len(match.groups()) > 2

    full_command_str = ''.join(match.groups())
    commands = full_command_str.split(' ')
    commands.pop()

    cmd = find_command(commands)

    priorOption = commands[len(commands) - 2] if len(commands) > 1 else None

    command_token = Name.InvalidCommand
    subcommand_token = Name.InvalidCommand

    if len(match.groups()) <= 4:
        if cmd:
            command_token = Text

            validate = bool(len(commands))
            if not validate: 
                cmd = find_command(['%s' % match.string])
                if cmd: validate = True
            else:
                if len(match.groups()) >= 4:
                    print(match)

            if validate:
                if (not cmd['isRoot'] and cmd['isShell']): command_token = Name.Label
                else: command_token = Name.Command

                if has_subcommand:
                    try:
                        super_command = deep_get(COMPLETION_TREE, *cmd['CommandTree'])
                        if super_command: subcommand_token = Name.SubCommand
                        else: subcommand_token = Name.Symbol
                    except: subcommand_token = Name.InvalidCommand


        yield (match.start(1), command_token, command)
        try: yield (match.start(2), Text, match.group(2))
        except: pass

        if has_subcommand:
            yield (match.start(3), subcommand_token, match.group(3))
            try: yield (match.start(4), Text, match.group(4))
            except: pass



_identifier = r"[a-zA-Z_][a-zA-Z0-9_\-]*"
_unquoted_string = "([a-zA-Z0-9{}]+)".format(re.escape(r"-_/#@£$€%*+~|<>?."))
_command = r"(:?[a-zA-Z_][a-zA-Z0-9_\-]*)"

class ShellLexer(RegexLexer):
    name = "Pretty Shell Lexer"
    flags = re.IGNORECASE

    tokens = {
        'root': [
            # (r"^SELECT\s", Name.Command, str("query")),

            # (r"\s+", Text),

            (r'^(\?|help)\s*$', Name.Help),
            (r'^(q|quit|exit)\s*$', Name.Exit),
            (r'^(cls|clear)\s*$', Name.Help),

            (r"(True|False|true|false)", Keyword),

            (r"\-?[0-9]+", Number.Integer),

            # (r"(" + _identifier + r")(\s*=\s*)", bygroups(Name.Key, Operator)),

            # Commands
            # (r"^" + _command + r"(\s+)" + _command + r"(\s+|$)", command_callback),
            # (r"^" + _command + r"(\s+|$)", command_callback),
            (r"(?<=^)*(((?<=\s)|^)(:?[a-zA-Z_][a-zA-Z0-9_\-]*)(\s+))", command_lexer),

            # Options
            (r"--(?<=\s--)[a-zA-Z0-9]+(?=\s|$)", Name.Tag),

            # (r"(" + _identifier + r")(\s*)", Name.Symbol),

            (r"'(''|[^'])*'", String.Single),
            (r'"(""|[^"])*"', String.Symbol),
            (r"[;:()\[\],\.]", Punctuation),
        ],
    }