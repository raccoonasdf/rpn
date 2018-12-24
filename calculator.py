from fractions import Fraction
import collections
import functools
import re
import string


class OperatorError(Exception):
    '''
    to be used for pretty messages on errors that have been explicitly
    accounted for
    '''
    pass


class Calculator:
    def __init__(self, base=10):
        self.operators = {
            # returns num
            '+':       ((Fraction, Fraction), lambda x, y: x+y),
            '-':       ((Fraction, Fraction), lambda x, y: x-y),
            '*':       ((object, Fraction), self._mul),
            '/':       ((Fraction, Fraction), Fraction),
            '%':       ((Fraction, Fraction), lambda x, y: x % y),
            '^':       ((Fraction, Fraction), lambda x, y: x**y),
            '<':       ((Fraction, Fraction), lambda x, y: min(x, y)),
            '>':       ((Fraction, Fraction), lambda x, y: max(x, y)),
            'abs':     ((Fraction,), abs),
            'ord':     ((str,), lambda x: (ord(char) for char in x)),
            'range':   ((Fraction, Fraction), lambda x, y: self._range(x, y)),
            'range\'': ((Fraction, Fraction, Fraction),
                        lambda x, y, z: self._range(x, y, z)),

            # returns sym
            'chr':     ((Fraction,), lambda x: chr(abs(round(x)))),

            # returns any
            ')':       ((), self._close_nest),
            'copy':    ((object,), lambda x: (x, x)),
            'first':   ((object, object), lambda x, y: x),
            'second':  ((object, object), lambda x, y: y),
            'swap':    ((object, object), lambda x, y: (y, x)),
            'get':     ((str,), self._envget),

            # returns nothing
            '(':       ((), self._open_nest),
            'base':    ((object,), self._setbase),
            'clear':   ((list,), lambda *x: None),
            'frac':    ((), self._togglefrac),  # TODO: use := in 3.8+
            'set':     ((object, str), self._envset),

            # contextual
            'eval':    ((str,), self.parse),
            'foldl':   ((list, str), self._fold),
            'foldr':   ((list, str),
                        lambda x, y: self._fold(x, y, right=True)),
            'map':     ((list, str), self._map),

            # aliases
            '**':      '^',
            'r':       'range',
            'r\'':     'range\'',
            'cp':      'copy',
            's':       'swap',
            'b':       'base',
            'c':       'clear',
            'f':       'frac',
            'e':       'eval',
            'fold':    'foldl'

        }
        self.macros = {
            'pre': {
                '(': ('(', '{}')
            },
            'post': {
                ')': ('{}', ')'),
                '$': (':{}', 'foldl'),
                '?': (':{}', 'get'),
                '.': (':{}', 'map'),
                '=': (':{}', 'set')
            }
        }
        self.stack = []
        self.stack_stack = [self.stack]
        self.env = {}
        self.base = base
        self.frac = True

    def _envget(self, key):
        try:
            return self.env[key]
        except KeyError:
            raise OperatorError(f'var :{key} not set')

    def _envset(self, value, key):
        self.env[key] = value

    def _open_nest(self):
        self.stack = []
        self.stack_stack.append(self.stack)

    def _close_nest(self):
        result = self.stack_stack.pop()
        try:
            self.stack = self.stack_stack[-1]
        except IndexError:
            raise OperatorError(f'already in outermost scope')
        return result

    @staticmethod
    def _mul(x, y):
        if isinstance(x, str):
            return [x]*round(y)
        else:
            return x*y
        pass

    @staticmethod
    def _range(start, end, step=Fraction(1)):
        if step == 0:
            raise OperatorError('step cannot be 0')
        elif step < 0 and start < end or step > 0 and start > end:
            raise OperatorError('range will never end')
        x = start
        while x <= end if start <= end else x >= end:
            yield x
            x += step

    def _setbase(self, base):
        if isinstance(base, str):
            bases = {'bin': 2, 'b': 2, 'sex': 6, 's': 6, 'oct': 8, 'o': 8,
                     'dec': 10, 'd': 10, 'doz': 12, 'hex': 16, 'h': 16,
                     'x': 16}
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
            self.base = round(base)

    def _togglefrac(self):
        self.frac = not self.frac

    def _map(self, stack, op):
        (types, f) = self.get_operator(op)
        if len(stack) < len(types):
            raise OperatorError(f'expected {len(types)} arguments')

        if len(types) > 1:
            args = self._pop_args(types[:-1], stack=stack)
            for value in stack:
                yield f(*args, self._assert_type(value, types[-1]))
        else:
            for value in stack:
                result = f(self._assert_type(value, types[0]))
                if result is not None:
                    yield f(self._assert_type(value, types[0]))

    def _fold(self, stack, op, right=False):
        if right:
            stack = reversed(stack)
        (types, f) = self.get_operator(op)
        if len(types) != 2:
            raise OperatorError(f'expected a 2-argument operator')
        return functools.reduce(f, stack)

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
            result = lookup[n % base]+result
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
        if m is None:  # TODO: use := in 3.8+
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

    def display_token(self, value):
        return self.Ftoa(value) if isinstance(value, Fraction) else ':'+value

    def _assert_type(self, value, type):
        type_strs = {object: 'any', Fraction: 'num', str: 'sym', list: 'stack'}
        if not isinstance(value, type):
            raise OperatorError(f'{self.display_token(value)} is not of type'
                                f' {type_strs[type]}')
        return value

    @staticmethod
    def _cast(value):
        if isinstance(value, (int, float)):
            return Fraction(value)
        elif isinstance(value, complex):
            raise OperatorError('nonreal result')
        return value

    def get_operator(self, name):
        try:
            op = self.operators[name]
            if isinstance(op, str):
                op = self.operators[op]
        except KeyError:
            raise OperatorError('operator not found')
        return op

    def _pop_args(self, types, stack=None):
        if stack is None:
            stack = self.stack

        def assert_types(values, types):
            return [self._assert_type(value, type)
                    for value, type in zip(values, types)]

        if len(types) == 0:
            return []
        elif len(types) <= len(stack) or types == (list,):
            result = []
            try:
                before = types.index(list)
                after = -len(types[before+1:])
                if after == 0:
                    after = None

                result += assert_types(stack[:before], types[:before])
                result.append(stack[before:after])
                if after is not None:
                    result += assert_types(stack[after:], types[after:])

                stack.clear()
            except ValueError:
                result = assert_types(stack[-len(types):], types)

                stack[:] = stack[:-len(types)]

            return result
        else:
            raise OperatorError(f'expected {len(types)} arguments')

    def _run_macros(self, token):
        for prefix, commands in self.macros['pre'].items():
            if token.startswith(prefix):
                for command in commands:
                    self.parse(command.format(token[1:]))
                return True
        for suffix, commands in self.macros['post'].items():
            if token.endswith(suffix):
                for command in commands:
                    self.parse(command.format(token[:-1]))
                return True
        return False

    def _append_stack(self, value):
        if value is not None:
            if (isinstance(value, collections.Iterable)
                    and not isinstance(value, str)):
                for item in value:
                    self.stack.append(self._cast(item))
            else:
                self.stack.append(self._cast(value))

    def parse(self, token):
        try:
            self._append_stack(self.atoF(token))
        except ValueError:
            if len(token) > 1:
                if token.startswith(':'):
                    self._append_stack(str(token[1:]))
                    return
                elif self._run_macros(token):
                    return

            (types, f) = self.get_operator(token)
            try:
                self._append_stack(f(*self._pop_args(types)))
            except ZeroDivisionError:
                raise OperatorError('division by zero')
