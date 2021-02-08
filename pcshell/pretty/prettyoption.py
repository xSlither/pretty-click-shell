from typing import List
import json

import click
from click.core import augment_usage_errors, invoke_param_callback


class PrettyOption(click.Option):
    def __init__(self, param_decls, choices=None, literal=None, literal_tuple_type: List[type] = None, **attrs):
        super(PrettyOption, self).__init__(param_decls, **attrs)
        self.choices = choices
        self.literal = literal
        self.literal_tuple_type = literal_tuple_type


    def get_help_record(self, ctx):
        if self.hidden: return None
        return super(PrettyOption, self).get_help_record(ctx)


    def handle_parse_result(self, ctx, opts, args):
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

        else:
            def parse_array(line: str) -> list:
                try:
                    if line.startswith('[') and line.endswith(']'):
                        return line
                except: pass
                raise click.BadParameter('Invalid Python Literal Provided: %s' % str(value))

            def parse_args() -> str:
                ret = ''
                if len(args):
                    for arg in args:
                        if arg[:-1].replace('.', '', 1).isdigit() or (arg[:-1].lower() == 'true' or arg[:-1].lower() == 'false'):
                            ret += "{}, ".format(arg[:-1])
                        else:
                            ret += '"{}"", '.format(arg[:-1])
                    return "{}]".format(ret.rstrip()[:-2])
                return ret

            def parse_value(val: str) -> str:
                val = val[1: -1]
                if val.replace('.', '', 1).isdigit() or (val.lower() == 'true' or val.lower() == 'false'): return val
                else: return '"%s"' % val


            with augment_usage_errors(ctx, param=self):
                try:
                    value = parse_value(self.consume_value(ctx, opts))
                    value = parse_array('[{}, {}'.format(value, parse_args()))
                    value = json.loads(value)

                    args = None
                except Exception as e:
                    raise click.BadParameter('Invalid Python Literal Provided: %s' % str(value))


        def check_tuple():
            if self.literal and self.literal_tuple_type:
                if len(value) == len(self.literal_tuple_type):
                    for i in range(0, len(value)):
                        if not type(value[i]) == self.literal_tuple_type[i]:
                            if str(self.literal_tuple_type[i]).startswith('Choice('): 
                                if value[i] in self.literal_tuple_type[i].choices: continue
                                raise click.BadArgumentUsage('"{}" is not a valid argument. Valid choices are: {}'.format(value[i], str(self.literal_tuple_type[i].choices)))
                            
                        else: continue

                        break

                raise click.BadParameter('Tuple type does not match.\n\n\tProvided: {}\n\tExpected: {}'.format(value, self.literal_tuple_type))

        check_tuple()
        if self.expose_value:
            ctx.params[self.name] = value

        return value, args