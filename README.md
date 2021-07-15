## pretty-click-shell :pager:
*Create shell applications using Click for Python, with several out-of-the-box bells and whistles for a snazzier look and simple customization*

### Features
`Pcshell`provides several features that piggyback off of the Click Framework to make writing intuitive, versatile Shell applications as simple as writing a standard Click CLI. This includes:

 - Pretty Formatting of all Help & Error text
 - Full Autocompletion for Click Groups, Commands, and Sub-Shells.
 - Automatic Lexing of your CLI
 - Support for Typed Tuple Literals as Option Parameters
 - Bult-in Shell Commands: repeat, clear screen, clear history, etc.
 - Command/Group Aliases
 - Suggestions for mistyped commands
 - Full support for Windows OS
 - Full customization of colors

![Pretty Click Shell Demo](https://github.com/xSlither/pretty-click-shell/blob/master/pcshell_demo.gif)

### Installing
Installing Pretty Click Shell is easy. Simply use PyPi to install the module. Please review the requirements before installing. 
```batch
pip install pcshell
```
*Warning: This package is currently in an **Alpha** state.*

**Windows Users**:
In order for Mouse Support to work for autocompletion prompts, **you will need to patch Prompt_Toolkit**. I have included the patch in [this repository](https://github.com/xSlither/pretty-click-shell/tree/master/setup). You can patch the*.py files yourself or use the `windows_patch.bat`.

If you do not care about mouse support, be sure to set `mouse_support=False` when initializing your Shell.

### Requirements
`Pcshell` is built for Windows OS. However, it should work with other systems as well, but it has never been tested.

`Pcshell` requires the following modules:

 - click==7.1.2
 - colorama

And, then **either**:

 - pyreadline

*Or*

 - prompt-toolkit==2.0.10
 - pygments

`Pcshell` uses Prompt Toolkit to provide Click autocompletion, lexing, and more- but it is not required. If you do not need want these features, then only `pyreadline` is required, and your Shell Application will function with these features simply absent.

Prompt Toolkit v.2.0.10 is specifically required at this time due to incompatibilities with the Windows Terminal in the latest version. This may change in the future.
Click v.7.1.2 is specifically required at this time due to breaking changes in >v.8.x.x

At this time, the [PyPi package](https://pypi.org/project/pcshell/) for `pcshell` requires all of these listed modules as dependencies to make for easier testing of the package, as most of the core features rely on Prompt Toolkit. If you are a minimalist, you can go ahead and uninstall what you don't need or disable the features when initializing your shell.

### Getting Started
Creating a new shell application is simple. You will only need to import `pcshell` and use this module in place of `click`, as appropriate.

To get started, take a look at these sample applications to get an understanding of all of the features `pcshell` has to offer:

 - [Bare Bones Shell Application](https://github.com/xSlither/pretty-click-shell/tree/master/testapp/python/simpapp.py)
 - [Pcshell Playground](https://github.com/xSlither/pretty-click-shell/tree/master/testapp/python/testapp.py)

Be sure to read the libraries docstrings, too, where appropriate for further details about keyword arguments,  constants, and methods / decorators.

### To-Do List:
These are additional features I would like to implement into `pcshell` in the future:

 - Prompt Toolkit "rprompt" for live analysis of command errors
 - Customizable Prompt Toolkit Toolbar for additional meta info/help text
 - Lexing for invalid typed tuple literal Option Parameters

### Feedback?
I wrote Pretty Click Shell because I wanted a versatile template for writing shell applications with my favorite CLI framework, Click, specifically on Windows. This grew into me learning a lot more about Prompt Toolkit and how I could integrate these features automatically with my Click apps.

If you have any suggestions or bugs to report, please create an issue here for me to review. Help me grow this project so that other developers on Windows OS can make some cool shell applications with Click :smile:
