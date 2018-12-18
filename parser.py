from calculator import *
import readline
import sys

calc = Calculator()

def read_lines(prompt=''):
    try:
        while True:
            yield input(prompt)
    except EOFError:
        return
    except KeyboardInterrupt:
        return

def tokenize(line):
    for expr in line.partition('#')[0].split(';'):
        yield expr.split()

def parse_print(line, simple=False):
    for tokens in tokenize(line):
        snap = calc.stack[:]
        for token in tokens:
            try:
                calc.parse(token)
            except OperatorError as e:
                print(f'!{e} (in "{token}")')
                calc.stack = snap
                break
        stack = ' '.join(calc.display_token(value) for value in calc.stack)
        if simple:
            print(f'{stack}')
        else:
            print(f'={stack}\t({calc.itoa(calc.base-1)}+1)')

prefix='?'
def parse(lines=read_lines(prefix), echo=False, simple=False):
    for line in lines:
        if echo:
            print(prefix+line)
        parse_print(line, simple)
        if not simple:
            print()
