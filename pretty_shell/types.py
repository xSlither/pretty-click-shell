from click.types import Tuple


class Tuple_IntString(Tuple):
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