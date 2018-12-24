from calculator import *
import readline
import sys


prefix = '?'


def read_lines(prompt=prefix):
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


def parse_print(calc, line, simple=False):
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


def parse(lines=read_lines(), echo=False, simple=False,
          calc=Calculator()):
    for line in lines:
        if echo:
            print(prefix+line)
        parse_print(calc, line, simple)
        if not simple:
            print()
