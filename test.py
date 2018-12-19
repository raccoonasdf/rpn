#!/bin/env python3

import parser
from calculator import Calculator
import itertools

calc = Calculator()

values = ('1', '0', '-1', '1/3', '-1/3', '1/100', '-1/100', ':a', '::')

tests = []
for op in calc.operators.items():
    if not isinstance(op[1], str):
        name = op[0]
        argc = len(op[1][0])
        for perm in itertools.permutations(values, argc):
            tests.append(' '.join(perm+(name,)))
            tests.append('c;:d b')

parser.parse(tests, echo=True, simple=True, calc=calc)
