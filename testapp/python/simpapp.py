import os
import pcshell
import prompt_toolkit


pcshell.globals.HISTORY_FILENAME = '.simpapp-history'
IsShell = pcshell.globals.__IsShell__



CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)

#-----------------------------------------------------------------------------------------------------------
def ShellStart():
    import platform
    if platform.system() == 'Windows':
        os.system('color 0a')


@pcshell.shell(
    prompt = 'simpapp', 
    intro = pcshell.chars.CLEAR_CONSOLE + pcshell.chars.IGNORE_LINE, 
    context_settings = CONTEXT_SETTINGS,
    before_start=ShellStart,
    mouse_support=False
)
def simpapp():
    """The Simple Shell Application"""
    pass
#-----------------------------------------------------------------------------------------------------------


def VerifyName(ctx: pcshell.Context, param, value: str) -> str:
    if not value or not len(value):
        if not ctx.resilient_parsing:
            pcshell.echo('Please tell me your name (cannot be null)')
            ctx.exit()
        else: return value
    return value


@simpapp.group(cls=pcshell.MultiCommandShell, context_settings=CONTEXT_SETTINGS)
def hello():
    """A Command Group"""
    pass


tuple_test_choice = pcshell.types.Choice(['choice1', 'choice2', 'choice3'], display_tags=['style fg=#d7ff00'])

@hello.command(['world', 'alias'], context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@pcshell.option('--data', default=[], literal_tuple_type=[str, float, bool, tuple_test_choice], help='An optional typed tuple literal parameter')
# @pcshell.option('--data2', default=[], literal_tuple_type=[bool, bool], help='A second typed tuple literal parameter', multiple=True)
@pcshell.argument('name', default=lambda: os.path.split(os.path.expanduser('~'))[-1], callback=VerifyName, type=str, help='Your Name')
# @pcshell.argument('name2', default='someone', type=str, help='Your Other Name')
# @pcshell.argument('name3', default='someone_else', type=str, help='Your Other Other Name')
@pcshell.repeatable
def helloworld(data, name):
    """Executes the Hello World Process"""
    
    try: from greetings import GetGreeting
    except: from .greetings import GetGreeting
    pcshell.echo('\n{} {}. Details are below:'.format(GetGreeting(), name))
    
    if IsShell:
        if data:
            pcshell.echo('\n\tProvided Optional Tuple Param: %s' % str(data))
            pcshell.echo('\tOptional Tuple Param Type is: %s' % type(data))
        # if data2:
        #     pcshell.echo('\n\tProvided Optional Tuple Param 2: %s' % str(data2))

        if not data: #and not data2:
            pcshell.echo('\n\tNo Optional Tuples were provided')
    return data


if __name__ == '__main__':
    try: simpapp()
    except Exception as e: 
        print(str(e)) 
    finally: print('')