from fractions import Fraction
import collections
import functools
import itertools
import re
import string

# these exceptions to be used for pretty messages on errors that have been
# explicitly accounted for
class OperatorError(Exception):
    pass

class Calculator:
    def __init__(self, base=10):
        self.operators = {
            '+':       self._guard(2, lambda x, y: x+y),
            '-':       self._guard(2, lambda x, y: x-y),
            '*':       self._guard(2, lambda x, y: x*y),
            '/':       self._guard(2, Fraction),
            '%':       self._guard(2, lambda x, y: x%y),
            '^':       self._guard(2, lambda x, y: x**y),
            '**':      '^',
            '<':       self._guard(2, lambda x, y: min(x, y)),
            '>':       self._guard(2, lambda x, y: max(x, y)),
            '<-':      (2, lambda x, y: x),
            '->':      (2, lambda x, y: y),
            'base':    (1, self._setbase),
            'b':       'base',
            'frac':    (0, self._togglefrac), #TODO: use := in 3.8+ for these
            'f':       'frac',
            'clear':   (-1, lambda *x: None),
            'c':       'clear',
            'copy':    (1, lambda x: (x, x)),
            'cp':      'copy',
            'eval':    (1, self.parse),
            'e':       'eval',
            'swap':    (2, lambda x, y: (y, x)),
            's':       'swap',
            'chr':     self._guard(1, lambda x: chr(round(x))),
            'ord':     self._guard(1, lambda x: (ord(char) for char in x)),
            'range':   (2, lambda x, y: range(round(x), round(y)+1)),
            'r':       'range',
            'range\'': (3, lambda x, y, z: range(round(x), round(y)+1, round(z))),
            'r\'':     'range\''
        }
        self.stack = []
        self.base = base
        self.frac = True

    @staticmethod
    def _guard(argc, f, exception=TypeError, msg='type mismatch'):
        def guarded(*args):
            try:
                return f(*args)
            except exception:
                raise OperatorError(msg)
        return (argc, guarded)
        
    def _setbase(self, base):
        if isinstance(base, str):
            bases = {'bin': 2, 'b': 2, 'sex': 6, 's': 6, 'oct': 8, 'o': 8,
                     'dec': 10, 'd': 10, 'doz': 12, 'hex': 16, 'h': 16, 'x': 16}
            try:
                self.base = bases[base]
            except KeyError:
                raise OperatorError(f'base name "{base}" not found')
        else:
            base = round(base)
            if base < 2:
                raise OperatorError(f'radix too small')
            elif base > 36:
                raise OperatorError(f'radix too large')
            self.base = base

    def _togglefrac(self):
        self.frac = not self.frac

    def itoa(self, n, base=None):
        if base is None:
            base = self.base

        sign = '-' if n < 0 else ''
        n = abs(n)
        # limited number of digit characters restricts the calculator to
        # a maximum of base 36
        lookup = string.digits + string.ascii_lowercase

        result = ''
        while n >= base:
            result = lookup[n%base]+result
            n //= base

        return sign+lookup[n]+result

    def Ftoa(self, n, base=None, frac=None, float_acc=16):
        if base is None:
            base = self.base
        if frac is None:
            frac = self.frac
        
        num, den = n.numerator, n.denominator
        if frac:
            num = self.itoa(num, base)
            if den == 1:
                return num
            else:
                den = self.itoa(den, base)
                return f'{num}/{den}'
        else:
            integral, num = divmod(num, den)
            integral = self.itoa(integral, base)
            if num:
                num *= base**float_acc//den
                num = self.itoa(num, base)
                fractional = '0'*(16-len(num))+num.rstrip('0')
                return f'{integral}.{fractional}'
            else:
                return integral

    def atoF(self, s, base=None):
        if base is None:
            base = self.base
            
        RATIONAL_FORMAT = re.compile(r"""
            \A\s*                               # optional whitespace at the start, then
            (?P<sign>[-+]?)                     # an optional sign, then
            (?=[\dA-Z]|\.[\dA-Z])               # lookahead for digit or .digit
            (?P<num>[\dA-Z]*)                   # numerator (possibly empty)
            (?:                                 # followed by
               (?:/(?P<denom>[\dA-Z]+))?        # an optional denominator
            |                                   # or
               (?:\.(?P<fractional>[\dA-Z]*))?  # an optional fractional part
               (?:E(?P<exp>[-+]?[\dA-Z]+))?     # and optional exponent
            )
            \s*\Z                               # and optional whitespace to finish
        """, re.VERBOSE | re.IGNORECASE)

        m = RATIONAL_FORMAT.match(s)
        if m is None: #TODO: use := in 3.8+
            raise ValueError(f'{s} is not a valid rational')

        num = int(m.group('num') or '0', base)
        den = m.group('denom')
        if den:
            den = int(den, base)
        else:
            den = 1
            fractional = m.group('fractional')
            if fractional:
                scale = base**len(fractional)
                num = num*scale+int(fractional)
                den *= scale

            exp = m.group('exp')
            if exp:
                exp = int(exp, base)
                if exp >= 0:
                    num *= base**exp
                else:
                    den *= base**-exp

        if m.group('sign') == '-':
            num = -num

        return Fraction(num, den)

    def atoi(self, s, base=None):
        if base is None:
            base = self.base

        return round(self.atoF(s, base))

    def parse(self, token):
        try: # is rational
            value = self.atoF(token)
        except ValueError:
            if token.startswith(':') and len(token) > 1: # is symbol
                value = str(token[1:])
            else: # is operator
                suffixes = ['$', '.']
                suffix = None
                for s in suffixes:
                    if token.endswith(s):
                        suffix = s
                        token = token.rstrip(s)

                try:
                    operator = self.operators[token]
                    if isinstance(operator, str): # check if operator is an alias
                        operator = self.operators[operator]
                except KeyError:
                    raise OperatorError(f'operator not found')

                (argc, f) = operator
                try:
                    if argc == -1: # entire stack
                        value = f(*self.stack)
                        self.stack = []
                    elif argc == 0: # no args
                        value = f()
                    elif argc > 0 and len(self.stack) >= argc:
                        if suffix == '$': # reduce
                            if argc != 2:
                                raise OperatorError(f'reduce needs 2 args')
                            value = functools.reduce(f, self.stack)
                            self.stack = []
                        elif suffix == '.': # map
                            if argc == 1:
                                value = map(f, self.stack)
                            else:
                                argc -= 1
                                args, self.stack = self.stack[-argc:], self.stack[:-argc]
                                repeated_args = (itertools.repeat(arg) for arg in args)
                                value = map(f, *repeated_args, self.stack)
                            self.stack = []
                        else: # normal
                            args, self.stack = self.stack[-argc:], self.stack[:-argc]
                            value = f(*args)
                    else: # fail
                        raise OperatorError(f'expected {argc} arguments')
                except ZeroDivisionError:
                    raise OperatorError(f'division by zero')
        if value is not None:
            if not isinstance(value, str) and isinstance(value, collections.Iterable):
                self.stack += value
            else:
                self.stack.append(value)
