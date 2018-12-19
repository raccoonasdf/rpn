# rpn
cool little reverse polish notation calculator i made for fun

## interface
simple commandline interface; input lines begin with `?`, output lines begin with `=`, error lines begin with `!`.

input lines will request a space-seperated list of tokens (detailed below). `;` can seperate lines, which is useful for viewing intermediate results because the stack is printed as output on the end of each line.

output lines will contain a space-seperated listing of each item in the stack, followed by a numerical representation of what base you're currently in (represented using the largest single digit plus one, because every base is base 10).

## tokens and their values

### numbers
you can input numbers as ratios (e.g. `1/2`) or integers with or without fractional part (e.g. `0.5`). numbers should retain their exact value as long as they remain rational.

### symbols
you can input symbols (really just strings) by prefixing them with a `:`. this is mainly useful to give non-numerical arguments to special functions, but you can do arithmetic on unicode values too, if you want.

### operators
you can operate on data in the stack using operator functions, which will take some number of arguments from the top of the stack and append its result(s). an operator which has exactly 2 arguments can operate in reduce mode on the whole stack by suffixing it with `$`. an operator which has 1 argument or more can operate in map mode on the whole stack by suffixing it with `.`.

## examples

### arithmetic
```
?2 2 +
=4      (9+1)
```

### map
```
?1 2 3 4;1 +.
=1 2 3 4        (9+1)
=2 3 4 5        (9+1)
```

### reduce
```
?1 2 3 4 +$
=10     (9+1)
```

### rationals and float approximation
```
?1/3 1/4 +; f
=7/12   (9+1)
=0.583333333333333      (9+1)
```

### number bases
```
?10;2 base;:hex base;:dec base
=10     (9+1)
=1010   (1+1)
=a      (f+1)
=10     (9+1)
```

### evaluating symbols
```
?2 2 :+; eval
=2 2 :+ (9+1)
=4      (9+1)
```

### character arithmetic
```
?:a; ord 1 + chr
=:a     (9+1)
=:b     (9+1)
```

### some other useful functions
```
?1 2
=1 2    (9+1)
?swap
=2 1    (9+1)
?-
=1      (9+1)
?copy
=1 1    (9+1)
?clear
=       (9+1)
?1 4 range; clear
=1 2 3 4        (9+1)
=       (9+1)
?1 5 2 range'
=1 3 5  (9+1)
```

## list of default operators
| name (alias) | arguments     | returns  | description                            |
|--------------|---------------|----------|----------------------------------------|
| +            | num, num      | num      | addition                               |
| -            | num, num      | num      | subtraction                            |
| *            | num, num      | num      | multiplication                         |
| /            | num, num      | num      | division                               |
| %            | num, num      | num      | modulo                                 |
| ^ (**)       | num, num      | num      | exponentation                          |
| <            | num, num      | num      | minimum                                |
| >            | num, num      | num      | maximum                                |
| abs          | num           | num      | absolute value                         |
| ord          | sym           | num      | symbol to number                       |
| range (r)    | num, num      | num\*    | generate number range                  |
| range' (r')  | num, num, num | num\*    | generate number range (with step size) |
| chr          | num           | sym      | number to symbol                       |
| <-           | any, any      | any      | first argument                         |
| ->           | any, any      | any      | second argument                        |
| copy (cp)    | any           | any, any | duplicate                              |
| swap (s)     | any, any      | any, any | swap order                             |
| base (b)     | any           |          | set base                               |
| clear (c)    | \*            |          | clear stack                            |
| frac (f)     |               |          | toggle float/fraction representation   |
| eval (e)     | sym           | varies   | evaluate symbol as operator            |
| foldl (fold) | \*, sym       | varies   | fold (left to right)                   |
| foldr        | \*, sym       | varies   | fold (right to left)                   |
| map          | \*, sym       | varies   | map                                    |

