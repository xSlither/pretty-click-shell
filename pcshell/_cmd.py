from typing import List
import inspect
import os
import sys

try: 
    import readline
except: pass

try:
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.shortcuts import PromptSession
    
    from prompt_toolkit.lexers import PygmentsLexer
except: pass

from cmd import Cmd

import click
from click._compat import raw_input as get_input

from colorama import Style

from . import globals as globs
from . import _colors as colors
from . import utils
from .chars import IGNORE_LINE

try:
    from ._completion import get_completer, BuildCompletionTree
except: pass


class ClickCmd(Cmd, object):
    """A custom Cmd implemenation that delegates output / exceptions to click, handles user input, and maintains a history file"""

    # Cmd string overrides
    identchars = Cmd.identchars + '-'
    nohelp = "No help on %s"
    nocommand = "\n\t{}Command not found: {}%s{}".format(colors.COMMAND_NOT_FOUND_TEXT_STYLE, colors.COMMAND_NOT_FOUND_TEXT_FORE, Style.RESET_ALL)

    def __init__(self, ctx: click.Context =None, 
    on_finished=None, hist_file=None, before_start=None, readline=None, 
    complete_while_typing=True, fuzzy_completion=True, mouse_support=True, *args, **kwargs):
        self._stdout = kwargs.get('stdout')
        super(ClickCmd, self).__init__(*args, **kwargs)

        # readline overrides
        self.old_completer = None
        self.old_delims = None
        self.readline = readline

        # Prompt Toolkit Settings
        self.complete_while_typing = complete_while_typing
        self.fuzzy_completion = fuzzy_completion
        self.mouse_support = mouse_support

        # A callback function that will be excuted before loading up the shell. 
        # By default this changes the color to 0a on a Windows machine
        self.before_start = before_start

        # Save the click.Context and callback for when the shell completes
        self.ctx = ctx
        self.on_finished = on_finished

        # Define the history file
        hist_file = hist_file or os.path.join(os.path.expanduser('~'), globs.HISTORY_FILENAME)
        self.hist_file = os.path.abspath(hist_file)
        if not os.path.isdir(os.path.dirname(self.hist_file)):
            os.makedirs(os.path.dirname(self.hist_file))

        self.history = FileHistory(self.hist_file)
        self.history.load_history_strings()


    def clear_history(self) -> bool:
        try:
            if self.readline: 
                readline.clear_history()
            else:
                if not len(self.prompter.history._loaded_strings): return True

                os.remove(self.hist_file)
                self.prompter.history._loaded_strings = []
            return True
                
        except Exception as e:
            return False


    # ----------------------------------------------------------------------------------------------
    # ANCHOR Cmd Loop Overrides
    # ----------------------------------------------------------------------------------------------

    def preloop(self):
        if self.readline:
            # Read history file when cmdloop() begins
            try: readline.read_history_file(self.hist_file)
            except IOError: pass

    def postloop(self):
        if self.readline:
            # Write history before cmdloop() returns
            try: 
                readline.set_history_length(1000)
                readline.write_history_file(self.hist_file)
            except IOError: pass

        # Invoke callback before shell closes
        if self.on_finished: self.on_finished(self.ctx)


    def cmdloop(self, intro=None):
        self.preloop()

        # Readline Handling
        if self.readline:
            if self.completekey and readline:
                self.old_completer = readline.get_completer()
                self.old_delims = readline.get_completer_delims()
                readline.set_completer(self.complete)
                readline.set_completer_delims(' \n\t')
                to_parse = self.completekey + ': complete'
                if readline.__doc__ and 'libedit' in readline.__doc__:
                    # Mac OSX
                    to_parse = 'bind ^I rl_complete'
                readline.parse_and_bind(to_parse)

        try:
            # Call an optional callback function before writing the intro and initializing/starting the shell
            if self.before_start:
                if callable(self.before_start): self.before_start()

            # Write an intro for the shell application
            if intro is not None:
                self.intro = intro
            if self.intro:
                click.echo(self.intro, file=self._stdout)
            stop = None

            if not self.readline:
                # Initialize Completion Tree for Master Shell
                if globs.__MASTER_SHELL__ == self.ctx.command.name:
                    BuildCompletionTree(self.ctx)

                # Initialize Prompter
                from ._lexer import ShellLexer
                from prompt_toolkit.styles import Style

                from pygments.styles import get_style_by_name
                from prompt_toolkit.styles.pygments import style_from_pygments_cls
                from prompt_toolkit.output.color_depth import ColorDepth

                prompt_style = Style.from_dict({
                    '': colors.PROMPT_DEFAULT_TEXT,

                    'name': colors.PROMPT_NAME,
                    'prompt': colors.PROMPT_SYMBOL,

                    'pygments.text': colors.PROMPT_DEFAULT_TEXT,
                    'pygments.name.help': colors.PYGMENTS_NAME_HELP,
                    'pygments.name.exit': colors.PYGMENTS_NAME_EXIT,
                    'pygments.name.symbol': colors.PYGMENTS_NAME_SYMBOL,

                    'pygments.name.label': colors.PYGMENTS_NAME_SHELL,

                    'pygments.name.invalidcommand': colors.PYGMENTS_NAME_INVALIDCOMMAND,
                    'pygments.name.command': colors.PYGMENTS_NAME_COMMAND,
                    'pygments.name.subcommand': colors.PYGMENTS_NAME_SUBCOMMAND,

                    'pygments.name.tag': colors.PYGMENTS_OPTION,

                    'pygments.operator': colors.PYGMENTS_OPERATOR,
                    'pygments.keyword': colors.PYGMENTS_KEYWORD,

                    'pygments.literal.number': colors.PYGMENTS_LITERAL_NUMBER,

                    'pygments.literal.string': colors.PYGMENTS_LITERAL_STRING,
                    'pygments.literal.string.symbol': colors.PYGMENTS_LITERAL_STRING_LITERAL
                })

                message = [
                    ('class:name', self.get_prompt()),
                    ('class:prompt', ' > '),
                ]

                self.prompter = PromptSession(
                    message,
                    style=prompt_style,
                    color_depth=ColorDepth.TRUE_COLOR,

                    history=self.history,
                    enable_history_search=not self.complete_while_typing,
                    mouse_support=self.mouse_support,
                    completer=get_completer(self.fuzzy_completion),
                    complete_in_thread=self.complete_while_typing,
                    complete_while_typing=self.complete_while_typing,
                    lexer=PygmentsLexer(ShellLexer),
                    
                )

            # Start Shell Application Loop
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    try:
                        if self.readline:
                            line = get_input(self.get_prompt())
                        else:
                            line = self.prompter.prompt()
                    except EOFError:
                        if not globs.__IS_REPEAT_EOF__:
                            # Exits the Shell Application when stdin stream ends
                            click.echo(file=self._stdout)
                            break
                        else:
                            # Swap STDIN from Programmatic Input back to User Input
                            globs.__IS_REPEAT_EOF__ = False
                            sys.stdin = globs.__PREV_STDIN__
                            # Prevent empty lines from being created from null input
                            print('\n' + IGNORE_LINE)
                            continue

                    except KeyboardInterrupt:
                        # Do not exit the shell on a keyboard interrupt
                        try:
                            if line != '': 
                                click.echo(file=self._stdout)
                                continue
                        except: pass

                        # Prevent empty lines from being created from null input
                        if not self.readline: click.echo(IGNORE_LINE)
                        else: print('\n' + IGNORE_LINE)

                        continue

                # Safely handle calling command and pretty-displaying output / errors
                if line.strip():
                    if globs.__IS_REPEAT__:
                        # If stream source is from the 'repeat' command, display the "visible" repeated command
                        click.echo(globs.__LAST_COMMAND_VISIBLE__)

                    try:
                        line = self.precmd(line)
                        stop = self.onecmd(line)
                        stop = self.postcmd(stop, line)
                        if not stop: 
                            line = ''
                            click.echo(file=self._stdout)
                    except KeyboardInterrupt:
                        click.echo(file=self._stdout)
                        continue
                    finally:
                        # Will tell the next loop to switch stdin back to user input after completing a "repeated" command
                        if line[0:6] != 'repeat' and globs.__IS_REPEAT__: 
                            globs.__IS_REPEAT__ = False
                            globs.__IS_REPEAT_EOF__ = True
                else:
                    # Prevent empty lines from being created from null input
                    if not self.readline: click.echo(IGNORE_LINE)
                    else: print(IGNORE_LINE)
                    continue

        finally:
            self.postloop()
            if self.completekey:
                try:
                    if self.readline:
                        readline.set_completer(self.old_completer)
                        readline.set_completer_delims(self.old_delims)
                except IOError: pass


    # ----------------------------------------------------------------------------------------------
    # ANCHOR Default Handling & Click Forwards
    # ----------------------------------------------------------------------------------------------

    def get_prompt(self):
        if callable(self.prompt):
            kwargs = {}
            if hasattr(inspect, 'signature'):
                sig = inspect.signature(self.prompt)
                if 'ctx' in sig.parameters:
                    kwargs['ctx'] = self.ctx
            return self.prompt(**kwargs)
        else: return self.prompt

    def emptyline(self):
        return False

    def default(self, line):
        self.VerifyCommand(line)

    def get_names(self):
        return dir(self)


    def VerifyCommand(self, line):
        commands = []
        names = self.get_names()

        for key in names:
            if not '--' in key:
                if 'do_' in key[0: 3]:
                    if not 'hidden_{}'.format(key[3:]) in names:
                        commands.append(key[3:])
                    elif 'orig_{}'.format(key[3:]) in names:
                        commands.append(key[3:])
                        
        suggest = utils.suggest(commands, line) if len(commands) else None
        click.echo(
            self.nocommand % line if not suggest else (self.nocommand % line) + '.\n\n\t{}{}Did you mean "{}{}{}"?{}'.format(
                colors.SUGGEST_TEXT_STYLE, colors.SUGGEST_TEXT_COLOR, colors.SUGGEST_ITEMS_STYLE, suggest, colors.SUGGEST_TEXT_COLOR, Style.RESET_ALL), 
            file=self._stdout
        )


    # ----------------------------------------------------------------------------------------------
    # ANCHOR Explicit Command definitions
    # ----------------------------------------------------------------------------------------------

    # Can be overrided by defined commands of the same name

    def do_exit(self, arg):
        return True

    def do_help(self, arg):
        if not arg:
            super(ClickCmd, self).do_help(arg)
            return

        try:
            func = getattr(self, 'help_' + arg)
        except AttributeError:
            try:
                do_fun = getattr(self, 'do_' + arg, None)

                if do_fun is None:
                    self.VerifyCommand(arg)
                    return

                doc = do_fun.__doc__
                if doc:
                    click.echo(doc, file=self._stdout)
                    return
            except AttributeError:
                pass
            click.echo(self.nohelp % arg, file=self._stdout)
            return
        func()


    # ----------------------------------------------------------------------------------------------
    # ANCHOR Default "Help" Overrides
    # ----------------------------------------------------------------------------------------------

    def __strip_hidden(self, cmds) -> List[str]:
        ret: List[str] = []
        for cmd in cmds:
            try:
                hidden: bool = getattr(self, 'hidden_' + cmd)
                if not hidden:
                    ret.append(cmd)
            except AttributeError:
                ret.append(cmd)
        return ret

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if header is not None:
            if cmds:
                click.echo(header, file=self._stdout)
                if Cmd.doc_header in header or Cmd.undoc_header in header:
                    cmds = self.__strip_hidden(cmds)

                if self.ruler:
                    click.echo(str(self.ruler * len(header)), file=self._stdout)
                self.columnize(cmds, maxcol - 1)
                click.echo(file=self._stdout)