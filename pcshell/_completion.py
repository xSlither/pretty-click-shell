from typing import List, Union, Tuple
from functools import reduce

import re
import json
import shlex

import click

from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.completion import (
    Completer, FuzzyCompleter, Completion
)

from .pretty import PrettyArgument, PrettyOption
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

    @staticmethod
    def get_true_option_from_line(line) -> str:
        tmp = line.rstrip()
        tmp = re.sub(r"((,[\s]*\])|(,[\s]*)|((,\][\s]*)))$", '', tmp)

        def read_words(words: List[str]) -> str:
            for word in reversed(words): 
                if word.startswith('--'): return word
            return None

        try:
            tmp_words = shlex.split(tmp, posix=False)
            return read_words(tmp_words)
        except:
            tmp_words = tmp.split(' ')
            if len(tmp_words) > 1:
                tmp_words.pop()
                return ClickCompleter.get_true_option_from_line(' '.join(tmp_words))
            elif len(tmp_words):
                try:
                    tmp_words = shlex.split(tmp, posix=False)
                    return read_words(tmp_words)
                except: return None
            else: return None


    @staticmethod
    def get_current_tuple_from_line(line) -> str:
        tmp = line.rstrip()
        tmp = re.sub(r"((,[\s]*\])|(,[\s]*)|((,\][\s]*)))$", '', tmp)

        # no_quotes = re.sub('".*?"', '', tmp)
        index = tmp.rfind('[', 0)
        index2 = tmp.rfind(']', index) if index >= 0 else -1

        ret = line[index:] if not index2 > index else None
        return ret



    def get_completions(self, document, complete_event):
        word: str = document.get_word_before_cursor()
        line: str = document.current_line_before_cursor

        original_line = line.rstrip()
        original_words = original_line.split(' ')
        original_words_prev = original_words.copy()
        original_words_prev.pop()

        line = ((' '.join(globs.__SHELL_PATH__) + ' ') if len(globs.__SHELL_PATH__) else '') + line

        words = line.rstrip().split(' ')
        lastword = words[len(words) - 1]
        priorOption = words[len(words) - 2] if len(words) > 1 else None

        try:
            current_key = []
            for i in range(0, len(words)):
                if i < len(globs.__SHELL_PATH__): continue

                try:
                    if deep_get(COMPLETION_TREE, *words[:len(words) - i]):
                        if len(original_words) > 2:
                            current_key = words[:(len(words) - (i - 1)) + len(globs.__SHELL_PATH__)]
                            if deep_get(COMPLETION_TREE, *current_key): break

                        elif '--' in lastword: 
                            current_key = words[:len(words) - i]
                        else: 
                            current_key = words[:len(words) - (i - 1)]
                            if deep_get(COMPLETION_TREE, *current_key): break

                    elif priorOption and '--' in priorOption:
                        current_key = words[:len(words) - (i + 1)]
                        if deep_get(COMPLETION_TREE, *current_key): break

                    else:
                        key = words[:len(words) - (i + 1)]
                        if deep_get(COMPLETION_TREE, *key):
                            current_key = key
                            break
                except: break

            obj = deep_get(COMPLETION_TREE, *current_key)
            obj2 = deep_get(COMPLETION_TREE, *words)

            true_option = ClickCompleter.get_true_option_from_line(line)

            l = len(words)
            c = len([x for x in words if '--' in x])
            l -= c if c else 0


            # Recommend Commands
        
            if obj:
                if obj2 and obj2['isGroup']:
                    commands = [k for k, v in obj2.items() if isinstance(obj2[k], dict) and not obj2[k]['isHidden']]
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
                            commands = [k for k, v in obj.items() if isinstance(obj[k], dict) and not obj[k]['isHidden']]
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

                    # Option Reflection Utilities
                    
                    def get_option(name: str) -> PrettyOption:
                        if len(obj['_options']):
                            try: return [x for x in obj['_options'] if x[0] == name][0][1]
                            except IndexError: pass
                        return None

                    
                    def get_option_names() -> List[str]:
                        expression = r'(?<=--)([a-zA-Z0-9]*)(?=\s)'
                        return re.findall(expression, line)


                    # HTML Display Style Utilities
                    
                    def get_option_display_tag(option, value, isChoice=False, isBool=False) -> List[str]:
                        tag = colors.COMPLETION_CHOICE_DEFAULT

                        if isChoice:
                            try:
                                if len(option.choices.display_tags):
                                    try:
                                        tag = option.choices.display_tags[values.index(value)]
                                    except: tag = option.choices.display_tags[values.pop()]
                            except: pass
                                
                            try:
                                if len(option.type.display_tags):
                                    try:
                                        tag = option.type.display_tags[values.index(value)]
                                    except: tag = option.type.display_tags[values.pop()]
                            except: pass

                        if isBool:
                            tag = colors.COMPLETION_CHOICE_BOOLEAN_TRUE if value == 'true' else colors.COMPLETION_CHOICE_BOOLEAN_FALSE

                        return tag

                    
                    def get_option_literal_tuple_display_tag(tuple_type, value) -> List[str]:
                        tag = colors.COMPLETION_CHOICE_DEFAULT

                        isChoice = False
                        isBool = False

                        if 'Choice(' in str(tuple_type): 
                            isChoice = True
                            values = [c for c in tuple_type.choices if c]
                        elif str(tuple_type) == 'bool': 
                            isBool = True
                            values = ['true', 'false']

                        if isChoice:
                            try:
                                if len(tuple_type.display_tags):
                                    try:
                                        tag = tuple_type.display_tags[values.index(value)]
                                    except: tag = tuple_type.display_tags[values.pop()]
                            except: pass

                        if isBool:
                            tag = colors.COMPLETION_CHOICE_BOOLEAN_TRUE if value == 'true' else colors.COMPLETION_CHOICE_BOOLEAN_FALSE

                        return tag

                    
                    # Typed Tuple Parameter Completion Support

                    def get_literal_tuple_display(option: PrettyOption, word: str, mod=0) -> Tuple[List[str], HTML, HTML, int]:
                        Current_Tag_Begin = '<u><b>'
                        Current_Tag_End = '</b></u>'

                        def fix_json_string(tmp) -> str:
                            """Transforms all \'\' and \`\` strings into \"\" strings"""
                            for match in re.finditer(r"(['`])(?:(?=(\\?))\2.)*?(\1)", tmp):
                                m = tmp[match.span()[0]: match.span()[1]]
                                if (m.startswith('"') or m.startswith("'") or m.startswith('`')) and (m.endswith('"') or m.endswith("'") or m.endswith('`')):
                                    tmp = tmp[:match.start()] + ('"%s"' % m[1:-1]) + tmp[match.span()[1]:]
                            return tmp

                        def get_valid_json(w: str, recurse=False) -> Union[list, None]:
                            tmp = w.rstrip()
                            tmp = re.sub(r"((,[\s]*\])|(,[\s]*)|((,\][\s]*)))$", '', tmp)
                            tmp = re.sub(r"([,]{1,999}.(?<=,))", ',', tmp)

                            tmp = fix_json_string(tmp)

                            if tmp.startswith('['):
                                try:
                                    if not tmp.endswith(']'): tmp += ']'
                                    return json.loads(tmp)
                                except:
                                    try: tmp_words = shlex.split(tmp, posix=False)
                                    except: tmp_words = tmp.split(' ')

                                    if len(tmp_words) > 1:
                                        tmp_words.pop()
                                        return get_valid_json(' '.join(tmp_words), True)
                                    elif len(tmp_words):
                                        try:
                                            tmp_words = shlex.split(' '.join(tmp_words).rstrip(), posix=False)
                                            return json.loads(' '.join(tmp_words))
                                        except: return None
                                    return None
                            return None

                        
                        def get_tuple_displaylist(cur_json: list, remaining=True) -> List[str]:
                            types = []
                            if len(cur_json) and (len(cur_json) < len(option.literal_tuple_type)):
                                if remaining:
                                    for tuple_type in option.literal_tuple_type[len(cur_json) + mod:]:
                                        types.append('<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE, html_escape(str(tuple_type))))
                                else:
                                    for tuple_type in option.literal_tuple_type[:len(cur_json) + mod]:
                                        types.append('<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE_USED, html_escape(str(tuple_type))))
                            elif len(cur_json) and not remaining:
                                for tuple_type in option.literal_tuple_type[:len(cur_json) + mod]:
                                    types.append('<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE_USED, html_escape(str(tuple_type))))
                            else:
                                if remaining:
                                    for tuple_type in option.literal_tuple_type[mod:]:
                                        types.append('<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE, html_escape(str(tuple_type))))
                                else:
                                    types.append('<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE_USED, html_escape(str(option.literal_tuple_type[0]))))
                            return types

                        
                        def get_tuple_values(used_types, cur_json) -> List[str]:
                            if not len(word.rstrip()): 
                                return ['[']
                            else:
                                if (len(cur_json) < len(option.literal_tuple_type) + mod):
                                    values = []
                                    isChoice = False
                                    isBool = False

                                    raw_type = option.literal_tuple_type[len(used_types) - 1 if len(used_types) else 0]
                                    type_str = str(raw_type)

                                    if  type_str.startswith('Choice('):
                                        isChoice = True
                                        values = ['"%s"' % c for c in raw_type.choices if c]

                                    elif "<class 'bool'>" in type_str: 
                                        isBool = True
                                        values = ['true', 'false']

                                    elif "<class 'float'>" in type_str:
                                        values.append('0.0')

                                    elif "<class 'int'>" in type_str:
                                        values.append('0')

                                    if not len(values): 
                                        values.append('\"\"')
                                    return values
                                else:
                                    return [']']

                        
                        def get_tuple_value_display(used_types, cur_json) -> str:
                            if not len(word.rstrip()): 
                                return '<b>[</b>'
                            elif len(used_types):
                                if (len(used_types) < len(option.literal_tuple_type)):
                                    return '<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE_CURRENT, html_escape(str(option.literal_tuple_type[len(used_types) - 1])))
                                else:
                                    return '<b>]</b>'
                            else: 
                                if len(cur_json):
                                    return '<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE_CURRENT, html_escape(str(option.literal_tuple_type[len(used_types) - 1])))
                                else:
                                    return '<style {}>{}</style>'.format(colors.COMPLETION_LITERAL_TUPLE_TYPE_CURRENT, html_escape(str(option.literal_tuple_type[0])))


                        word_json = get_valid_json(word)
                        if not word_json: word_json = []

                        if len(word_json) >= len(option.literal_tuple_type): mod -= 1

                        used_types = get_tuple_displaylist(word_json, False)
                        remaining_types = get_tuple_displaylist(word_json)
                        vals = get_tuple_values(used_types, word_json)

                        disp_val = get_tuple_value_display(used_types, word_json)

                        index = len(word_json) - 1
                        disp = '<b>[</b>'
                        if len(used_types):
                            disp += ', '.join(used_types)
                        if len(used_types) < len(option.literal_tuple_type):
                            disp += ', ' + ', '.join(remaining_types)
                        disp += '<b>]</b>'

                        if index > -1:
                            disp = disp.replace(used_types[index + mod], '{}{}{}'.format(Current_Tag_Begin, used_types[index + mod], Current_Tag_End))
                        elif len(used_types):
                            disp = disp.replace(used_types[0], '{}{}{}'.format(Current_Tag_Begin, used_types[0], Current_Tag_End))

                        return (vals, HTML(disp_val), HTML(disp), index + mod)


                    # Recommend Option Parameters

                    if len(obj['_options']):
                        valid = True
                        option = get_option(true_option)

                        def get_option_args():
                            ret = []
                            for arg in reversed(original_words):
                                if arg == true_option: break
                                ret.append(arg)
                            return ret

                        if option:
                            option_nargs = 1
                            option_args = get_option_args()

                            if HasKey('nargs', option): option_nargs = option.nargs
                            if len(option_args):
                                if not option.literal_tuple_type:
                                    if len(option_args) >= option_nargs: valid = False
                                else:
                                    if ']' in option_args[0]: valid = False

                            if (not option.multiple) and (original_words_prev.count('--%s' % option.name) > 1):
                                valid = False

                        if option and valid:
                            if not (option.is_bool_flag or option.is_flag):
                                values = []
                                isChoice = False
                                isBool = False

                                invalid = False

                                if not option.literal:
                                    # Option Parmeter is standard
                                    disp_meta = None

                                    if not '.Tuple object' in str(option.type):
                                        # Standard Parameter
                                        if option.type.name == 'choice':
                                            isChoice = True
                                            values = [c for c in option.type.choices if c]
                                        elif option.choices and ('Choice' in str(type(option.choices))): 
                                            isChoice = True
                                            values = [c for c in option.choices.choices if c]
                                        elif option.type.name == 'boolean': 
                                            isBool = True
                                            values = ['true', 'false']
                                        elif option.type.name == 'float':
                                            values = ['0.0']
                                        elif option.type.name == 'integer':
                                            values = ['0']
                                        elif option.type.name == 'text':
                                            values = ['""']

                                        if not isChoice and not isBool:
                                            meta_name = ('&#60;class :%s:&#62;' % option.type.name)
                                            disp_meta = HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_OPTION_DESCRIPTION, meta_name))
                                    else:
                                        # Click Tuple Type

                                        option_args = get_option_args()
                                        if len(option_args) > option.nargs:
                                            return

                                        type_obj = option.type.types[::-1][len(option_args) - 1]

                                        if type_obj:
                                            type_name = type_obj.name
                                            if type_name == 'choice':
                                                values = [c for c in type_obj.choices if c]
                                                isChoice = True
                                            elif type_name == 'boolean':
                                                isBool = True
                                                values = ['true', 'false']
                                            elif type_name == 'float':
                                                values = ['0.0']
                                            elif type_name == 'integer':
                                                values = ['0']
                                            elif type_name == 'text':
                                                values = ['""']

                                        if not isChoice and not isBool:
                                            meta_name = ('&#60;class :%s:&#62;' % type_name)
                                            disp_meta = HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_OPTION_DESCRIPTION, meta_name))

                                    for value in values:
                                        if value.startswith(word):
                                            tag = get_option_display_tag(option, value, isChoice=isChoice, isBool=isBool)

                                            yield Completion(
                                                value,
                                                start_position=-len(word),
                                                display=HTML("<{}>{}</{}>".format(
                                                    tag,
                                                    value,
                                                    tag if not 'style' in tag else 'style'
                                                )),
                                                display_meta=disp_meta
                                            )

                                else:
                                    # Option Parameter is a Typed Tuple

                                    if option.literal_tuple_type:
                                        def fixTupleSpacing(val):
                                            val = re.sub(r"(\[[\s])", '[', val)
                                            val = re.sub(r"([\s]\])", ']', val)
                                            val = re.sub(r"(\[,)", ']', val)
                                            val = re.sub(r"(,\])", ']', val)
                                            val = re.sub(r"(\",\")", "\", \"", val)
                                            val = re.sub(r"([,]{1,999}.(?<=,))", ',', val)
                                            return val

                                        def lastword_is_option() -> bool:
                                            _line_ = original_line.rstrip()
                                            l = len(_line_)
                                            l2 = len(option.name)
                                            return (_line_[(l - l2) - 2:] == '--%s' % option.name) if l > 2 else False

                                        mod = 1
                                        orig_tuple = ClickCompleter.get_current_tuple_from_line(line)
                                        true_tuple = orig_tuple

                                        if not orig_tuple:
                                            if lastword_is_option(): orig_tuple = ' '
                                            else: invalid = True

                                        if orig_tuple: true_tuple = re.sub(r"((,[\s]*\])|(,[\s]*)|((,\][\s]*)))$", '', orig_tuple)

                                        if not invalid and (true_tuple and true_tuple.endswith(']')): invalid = True
                                        # if re.search(r"(((,[\s]*\])|(,[\s]*)|((,\][\s]*)))$)|((\"[\s]*,[\s]*\")(?![\w|\W]*\"))", orig_tuple): mod = 1

                                        if not invalid:
                                            try: completion_data = get_literal_tuple_display(option, true_tuple, mod)
                                            except Exception as e: return

                                            values = completion_data[0]
                                            disp = completion_data[1]
                                            disp_meta = completion_data[2]
                                            index = completion_data[3]

                                            if len(values) == 1:
                                                if (not values[0] == ']' and not values[0] == '[') and (index + mod < len(option.literal_tuple_type)):
                                                    values[0] += ','
                                                yield Completion(
                                                    fixTupleSpacing(orig_tuple + (values[0])),
                                                    start_position=-len(orig_tuple),
                                                    display=disp,
                                                    display_meta=disp_meta
                                                )
                                            elif len(values):

                                                i = 0
                                                tmp = word.rstrip()
                                                tmp = re.sub(r"((,[\s]*\])|(,[\s]*)|((,\][\s]*)))$", '', tmp)
                                                if not tmp.endswith(']'): tmp += ']'

                                                try: tmp_words = shlex.split(tmp, posix=False)
                                                except: tmp_words = tmp.split(' ')

                                                for value in values:
                                                    tag = get_option_literal_tuple_display_tag(option.literal_tuple_type[i], value)

                                                    if (not value == ']' and not value == '[') and (index + mod < len(option.literal_tuple_type)):
                                                        value += ','

                                                    yield Completion(
                                                        fixTupleSpacing(orig_tuple + (value)),
                                                        start_position=-len(orig_tuple),
                                                        display= HTML("<{}>{}</{}>".format(
                                                            tag,
                                                            value,
                                                            tag if not 'style' in tag else 'style'
                                                        )),
                                                        display_meta=disp_meta
                                                    )
                                                    i += 1
                                # --------------------------------------------------------------------------------------------------------------------
                                if not invalid: return


                    # Recommend Options

                    if len(obj['_options']):
                        current_option = get_option(true_option)
                        for opt in obj['_options']:
                            name = opt[0]
                            option: click.Option = opt[1]

                            if name == '--help' or name == '-h': continue
                            if option.hidden: continue
                            if current_option and option.name == current_option.name:
                                if (option.is_bool_flag or option.is_flag) and not option.multiple: continue

                            if (not original_words_prev.count('--%s' % option.name) > 0) or option.multiple:
                                if name.startswith(word):
                                    h = html_escape(option.help) if option.help else ''
                                    meta_text = '{}{}'.format('(Optional) ' if not option.required else '', h)

                                    yield Completion(
                                        name,
                                        start_position=-len(word),
                                        display=HTML("<%s>%s</%s>" % (colors.COMPLETION_OPTION_NAME, name, colors.COMPLETION_OPTION_NAME)),
                                        display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_OPTION_DESCRIPTION, meta_text))
                                    )

                    # Recommend Arguments

                    if len(obj['_arguments']):

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

                        def get_argument_display_tag(arg: PrettyArgument, value, isChoice=False, isBool=False) -> List[str]:
                            tag = colors.COMPLETION_CHOICE_DEFAULT

                            if isChoice:
                                try:
                                    if len(arg.choices.display_tags):
                                        try:
                                            tag = arg.choices.display_tags[values.index(value)]
                                        except: tag = arg.choices.display_tags[values.pop()]
                                except: pass

                                try:
                                    if len(arg.type.display_tags):
                                        try:
                                            tag = arg.type.display_tags[values.index(value)]
                                        except: tag = arg.type.display_tags[values.pop()]
                                except: pass

                            if isBool:
                                tag = colors.COMPLETION_CHOICE_BOOLEAN_TRUE if value == 'true' else colors.COMPLETION_CHOICE_BOOLEAN_FALSE

                            return tag


                        words_len = len(words) - len(current_key)
                        words_len -= check_literal()

                        nargs = words_len + 1
                        nargs -= AnalyzeOptions()
                        nargs_count = nargs - AnalyzeArgs()
                        narg_map = getNargMap()
                        narg_count_map = getNargCountMap()

                        if nargs_count - 1 < len(obj['_arguments']):
                            arg_index = nargs - 1 if nargs > 0 else 0

                            arg = obj['_arguments'][narg_map[arg_index]]

                            name = arg[0]
                            argument: PrettyArgument = arg[1]
                            values = arg[2]

                            h = html_escape(argument.help) if argument.help else ''

                            isChoice = bool(argument.type.name == 'choice' or argument.choices)
                            isBool = argument.type.name == 'boolean'
                            isTuple = ' ' in argument.type.name

                            if isTuple:
                                type_obj = argument.type.types[narg_count_map[arg_index]]

                                _values = []
                                disp_meta = None

                                if type_obj:
                                    type_name = type_obj.name
                                    if type_name == 'choice':
                                        _values = [c for c in type_obj.choices if c]
                                        isChoice = True
                                    elif type_name == 'boolean':
                                        isBool = True
                                        _values = ['true', 'false']
                                    elif type_name == 'float':
                                        _values = ['0.0']
                                    elif type_name == 'integer':
                                        _values = ['0']
                                    elif type_name == 'text':
                                        _values = ['""']

                                if not isChoice and not isBool: meta_name = ('&#60;class :%s:&#62;' % type_name)
                                else: meta_name = '&#60;class :choice:&#62;' if isChoice else '&#60;class :bool:&#62;'

                                meta_text = '{}{}'.format('(Optional) ' if not argument.required else '', h)
                                meta_value = '{} {}'.format(meta_name, meta_text)
                                disp_meta = HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_ARGUMENT_DESCRIPTION, meta_value))

                                for value in _values:
                                    tag = get_argument_display_tag(argument, value, isChoice, isBool)

                                    yield Completion(
                                        value,
                                        start_position=0,
                                        display=HTML("<{}>{}</{}>".format(
                                            tag,
                                            value,
                                            tag if not 'style' in tag else 'style'
                                        )),
                                        display_meta = disp_meta
                                    )

                            elif isChoice or isBool:
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
                                                tag if not 'style' in tag else 'style'
                                            ))
                                        )
                            else:
                                val = ' '
                                if argument.type.name == 'float': val = '0.0'
                                if argument.type.name == 'integer': val = '0'
                                if argument.type.name == 'text': val = '""'

                                meta_text = '{}{}'.format('(Optional) ' if not argument.required else '', h)

                                yield Completion(
                                    val,
                                    start_position=0,
                                    display=HTML("<%s>%s</%s>" % (colors.COMPLETION_ARGUMENT_NAME, name, colors.COMPLETION_ARGUMENT_NAME)),
                                    display_meta=HTML("<style %s><i>%s</i></style>" % (colors.COMPLETION_ARGUMENT_DESCRIPTION, meta_text))
                                )

        except Exception as e: return


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
                # if cmd.hidden: continue

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
                previous_parent_tree = []
                current_parent_tree = []

                for parent in parents:
                    current_parent_tree.append(parent)
                    if not deep_get(COMPLETION_TREE, *current_parent_tree):
                        deep_set(COMPLETION_TREE, { 
                            "isGroup": True, 
                            "isRoot": False,
                            "CommandTree": previous_parent_tree
                        }, *current_parent_tree)
                        previous_parent_tree.append(parent)

        keys = parents.copy()
        if not isinstance(cmd, click.Group):
            keys.append(cmd.name)
            deep_set(COMPLETION_TREE, {
                "isGroup": False,
                "CommandTree": parents,
                "isShell": False,
                "isRoot": False,
                "isHidden": cmd.hidden,
                "_options": opts,
                "_arguments": args,
                "_help": cmd.short_help or cmd.help
            }, *keys)

        elif not root:
            from .shell import Shell
            keys.append(cmd.name)
            dic = deep_get(COMPLETION_TREE, *keys)

            if not dic:
                deep_set(COMPLETION_TREE, {
                    "isGroup": True,
                    "CommandTree": parents,
                    "isShell": bool(isinstance(cmd, Shell) and cmd.isShell),
                    "isRoot": False,
                    "isHidden": cmd.hidden,
                    "_options": opts,
                    "_arguments": args,
                    "_help": cmd.short_help or cmd.help
                }, *keys)

            else:
                dic['isShell'] = bool(isinstance(cmd, Shell) and cmd.isShell)
                dic['isHidden'] = cmd.hidden
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