"""PatronCalc 64-bit programmer arithmetic, no eval or execution."""
import ast
import re

BITS = (8, 16, 32, 64)
BASES = {'HEX': 16, 'DEC': 10, 'OCT': 8, 'BIN': 2}
class ProgrammerError(ValueError):
    pass

def unsigned(value, bits=64):
    if bits not in BITS: raise ProgrammerError('Unsupported word size')
    return int(value) & ((1 << bits) - 1)

def signed(value, bits=64):
    value = unsigned(value, bits)
    return value - (1 << bits) if value & (1 << (bits - 1)) else value

def display(value, bits=64):
    v = unsigned(value, bits)
    return {'HEX': f'{v:0{bits//4}X}', 'DEC': str(signed(v, bits)),
            'OCT': format(v, 'o').zfill((bits + 2)//3), 'BIN': format(v, f'0{bits}b')}

def parse_value(text, base='DEC', bits=64):
    if base not in BASES: raise ProgrammerError('Invalid base')
    if not isinstance(text, str) or not text.strip() or len(text) > 90:
        raise ProgrammerError('Invalid integer')
    s = text.strip().replace('_', '')
    if not re.fullmatch(r'-?[0-9a-fA-F]+', s): raise ProgrammerError('Invalid digits')
    try: value = int(s, BASES[base])
    except ValueError as exc: raise ProgrammerError('Digit not valid for this base') from exc
    return unsigned(value, bits)

def operate(a, op, b=None, bits=64):
    if bits not in BITS: raise ProgrammerError('Invalid word size')
    x = unsigned(a, bits)
    y = unsigned(b, bits) if b is not None else None
    if op == 'NOT': return unsigned(~x, bits)
    if y is None: raise ProgrammerError('Missing operand')
    if op == 'AND': return x & y
    if op == 'OR': return x | y
    if op == 'XOR': return x ^ y
    if op == '+': return unsigned(x + y, bits)
    if op == '-': return unsigned(x - y, bits)
    if op == '*': return unsigned(x * y, bits)
    if op in ('<<', '>>'):
        if y >= bits: raise ProgrammerError('Shift count must be less than word size')
        return unsigned(x << y if op == '<<' else x >> y, bits)
    if op == '/':
        if y == 0: raise ProgrammerError('Cannot divide by zero')
        a, b = signed(x, bits), signed(y, bits)
        quotient = abs(a) // abs(b)
        return unsigned(-quotient if (a < 0) != (b < 0) else quotient, bits)
    if op == '%':
        if y == 0: raise ProgrammerError('Cannot divide by zero')
        return unsigned(x % y, bits)
    raise ProgrammerError('Unknown operation')
