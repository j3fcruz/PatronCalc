"""Restricted, Decimal-based calculator engine (no eval/exec)."""
import ast
import math
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

class CalculatorError(ValueError):
    pass

PI = Decimal('3.1415926535897932384626433832795028841971693993751')
E = Decimal('2.7182818284590452353602874713526624977572470936999')


def _function(name: str, value: Decimal, angle_mode: str) -> Decimal:
    if name == 'abs': return abs(value)
    if name == 'sqrt':
        if value < 0: raise CalculatorError('Square root requires a nonnegative number')
        return value.sqrt()
    if name == 'fact':
        if value != value.to_integral_value() or value < 0 or value > 200:
            raise CalculatorError('Factorial requires an integer from 0 to 200')
        return Decimal(math.factorial(int(value)))
    if name == 'inv':
        if not value: raise CalculatorError('Cannot divide by zero')
        return Decimal(1) / value
    if name == 'log':
        if value <= 0: raise CalculatorError('Logarithm requires positive input')
        return value.log10()
    if name == 'ln':
        if value <= 0: raise CalculatorError('Logarithm requires positive input')
        return value.ln()
    if name in ('sin','cos','tan'):
        if abs(value) > Decimal('1e12'):
            raise CalculatorError('Trigonometric input too large')
        radians = float(value if angle_mode == 'RAD' else value * PI / 180)
        if name == 'tan' and abs(math.cos(radians)) < 1e-12:
            raise CalculatorError('Tangent undefined at this angle')
        ans = getattr(math, name)(radians)
        if not math.isfinite(ans): raise CalculatorError('Result out of range')
        if abs(ans) < 1e-14: ans = 0.0
        return Decimal(str(ans))
    raise CalculatorError('Unsupported function')


def evaluate(expression: str, angle_mode: str = 'DEG') -> Decimal:
    if not isinstance(expression, str) or not expression or len(expression) > 160:
        raise CalculatorError('Empty or oversized expression')
    if angle_mode not in ('DEG', 'RAD'): raise CalculatorError('Invalid angle mode')
    try:
        tree = ast.parse(expression, mode='eval').body
    except SyntaxError as exc:
        raise CalculatorError('Incomplete expression') from exc
    def walk(node, depth=0):
        if depth > 24:
            raise CalculatorError('Expression too complex')
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            literal = ast.get_source_segment(expression, node) or str(node.value)
            if len(literal) > 80:
                raise CalculatorError('Number too long')
            return Decimal(literal)
        if isinstance(node, ast.Name):
            if node.id == 'pi': return +PI
            if node.id == 'e': return +E
            raise CalculatorError('Unknown constant')
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.keywords or len(node.args) != 1:
                raise CalculatorError('Unsupported function call')
            return _function(node.func.id, walk(node.args[0], depth+1), angle_mode)
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.USub, ast.UAdd):
            x = walk(node.operand, depth+1)
            return -x if isinstance(node.op, ast.USub) else x
        if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow):
            left, right = walk(node.left, depth+1), walk(node.right, depth+1)
            if isinstance(node.op, ast.Pow):
                if right != right.to_integral_value() or abs(right) > 1000:
                    raise CalculatorError('Power exponent must be an integer from -1000 to 1000')
                if left and abs(left.adjusted()) * abs(int(right)) > 900:
                    raise CalculatorError('Power result too large')
                if left == 0 and right < 0: raise CalculatorError('Cannot divide by zero')
                return left ** int(right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if right == 0: raise CalculatorError('Cannot divide by zero')
            return left / right
        raise CalculatorError('Unsupported expression')
    try:
        with localcontext() as ctx:
            ctx.prec = 28
            ctx.Emax = 999
            ctx.Emin = -999
            result = walk(tree)
            if not result.is_finite(): raise CalculatorError('Result out of range')
            return +result
    except (InvalidOperation, DivisionByZero, OverflowError, ArithmeticError, ValueError) as exc:
        raise CalculatorError('Invalid calculation or result out of range') from exc

def format_number(number: Decimal) -> str:
    if not number.is_finite(): raise CalculatorError('Non-finite result')
    if number.is_zero(): return '0'
    if number.adjusted() > 16 or number.adjusted() < -10:
        return format(number.normalize(), '.12E').replace('E+', 'e+').replace('E-', 'e-').replace('E', 'e')
    return format(number.normalize(), 'f')
