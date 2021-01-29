from typing import List
import inspect
import os
import sys

import readline

from cmd import Cmd

import click
from click._compat import raw_input as get_input

from colorama import Fore, Style

from . import globals as globs
from . import utils
from .chars import IGNORE_LINE


DEFAULT_HISTORY_FILENAME = '.pcshell-history'


class ClickCmd(Cmd, object):
    """A custom Cmd implemenation that delegates output / exceptions to click, handles user input, and maintains a history file"""

    # Cmd string overrides
    identchars = Cmd.identchars + '-'
    nohelp = "No help on %s"
    nocommand = "\n\t{}Command not found: {}%s{}".format(Style.DIM, Fore.YELLOW, Style.RESET_ALL)

    def __init__(self, ctx: click.Context =None, on_finished=None, hist_file=None, 
    system_cmd=None, *args, **kwargs):
        self._stdout = kwargs.get('stdout')
        super(ClickCmd, self).__init__(*args, **kwargs)

        # readline overrides
        self.old_completer = None
        self.old_delims = None

        # A system command that will be excuted before loading up the shell. 
        # By default this changes the color to 0a on a Windows machine
        self.system_cmd = system_cmd

        # Save the click.Context and callback for when the shell completes
        self.ctx = ctx
        self.on_finished = on_finished

        # Define the history file path / create path directories if applicable
        hist_file = hist_file or os.path.join(os.path.expanduser('~'), DEFAULT_HISTORY_FILENAME)
        self.hist_file = os.path.abspath(hist_file)
        if not os.path.isdir(os.path.dirname(self.hist_file)):
            os.makedirs(os.path.dirname(self.hist_file))


    def clear_history(self) -> bool:
        try:
            os.remove(self.hist_file)
            readline.read_history_file(self.hist_file)
            readline.set_history_length(1000)
            readline.write_history_file(self.hist_file)
            return True
            
        except Exception as e:
            return False


    # ----------------------------------------------------------------------------------------------
    # ANCHOR Cmd Loop Overrides
    # ----------------------------------------------------------------------------------------------

    def preloop(self):
        # Read history file when cmdloop() begins
        try: readline.read_history_file(self.hist_file)
        except IOError: pass

    def postloop(self):
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
        if self.completekey and readline:
            self.old_completer = readline.get_completer()
            self.old_delims = readline.get_completer_delims()
            readline.set_completer(self.complete)
            readline.set_completer_delims(' \n\t')
            to_parse = self.completekey + ': complete'
            if readline.__doc__ and 'libedit' in readline.__doc__:
                # Special case for mac OSX
                to_parse = 'bind ^I rl_complete'
            readline.parse_and_bind(to_parse)

        try:
            # Call an optional system command before writing the intro
            if self.system_cmd:
                os.system(self.system_cmd)

            # Write an "intro" for the shell application
            if intro is not None:
                self.intro = intro
            if self.intro:
                click.echo(self.intro, file=self._stdout)
            stop = None

            # Start Shell Application Loop
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    try:
                        line = get_input(self.get_prompt())
                    except EOFError:
                        if not globs.__IS_REPEAT_EOF__:
                            # Exits the Shell Application when stdin stream ends
                            click.echo(file=self._stdout)
                            break
                        else:
                            # Swap STDIN from Programmatic Input back to User Input
                            globs.__IS_REPEAT_EOF__ = False
                            sys.stdin = globs.__PREV_STDIN__
                            print('\n' + IGNORE_LINE) # Prevent empty lines from being created from null input
                            continue

                    except KeyboardInterrupt:
                        # Do not exit the shell on a keyboard interrupt
                        try:
                            if line != '': 
                                click.echo(file=self._stdout)
                                continue
                        except: pass

                        print('\n' + IGNORE_LINE)  # Prevent empty lines from being created from null input
                        continue

                # Safely handle calling command and pretty-displaying output / errors
                if line != '':
                    if globs.__IS_REPEAT__:
                        # If stream source is from the 'repeat' command, display the "visible" repeated command
                        print(globs.__LAST_COMMAND_VISIBLE__)

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
                    print(IGNORE_LINE) 
                    continue

        finally:
            self.postloop()
            if self.completekey:
                try:
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
            self.nocommand % line if not suggest else (self.nocommand % line) + '.\n\n\t{}Did you mean "{}{}{}"?{}'.format(
                Style.BRIGHT + Fore.CYAN, Fore.YELLOW, suggest, Fore.CYAN, Style.RESET_ALL), 
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