import click


class Choice(click.Choice):
    def __init__(self, choices, display_tags=None, case_sensitive=True):
        self.display_tags = display_tags
        # if self.display_tags and (not len(choices) == len(display_tags)): raise Exception('list "choices" does not match length of list "display_tags"')
        super(Choice, self).__init__(choices, case_sensitive=case_sensitive)


class Tuple_IntString(click.Tuple):
    def convert(self, value, param, ctx):
        if type(value) is str: 
            value = value.split()
            value[0] = int(value[0])

        if len(value) != len(self.types):
            raise ValueError('Tuple provided does not match type: <INT, STR>')

        return super(Tuple_IntString, self).convert(value, param, ctx) 


class HiddenPassword(object):
    def __init__(self, password=''):
        self.password = password
    
    def __str__(self):
        return '*' * len(self.password) if len(self.password) <= 16 else '*' * 16