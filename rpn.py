#!/bin/env python3

import argparse
import parser

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('expression', nargs='?',
    help='expression to pass to the calculator. leave empty for interactive')
args = arg_parser.parse_args()

if args.expression:
    parser.parse(args.expression.splitlines(), simple=True)
else:
    parser.parse()
