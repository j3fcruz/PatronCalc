import unittest
from decimal import Decimal
from engine import evaluate, format_number, CalculatorError

class EngineTests(unittest.TestCase):
    def test_precedence(self): self.assertEqual(evaluate('2+3*4'), Decimal(14))
    def test_parentheses(self): self.assertEqual(evaluate('(2+3)*4'), Decimal(20))
    def test_precision(self): self.assertEqual(evaluate('0.1+0.2'), Decimal('0.3'))
    def test_negative(self): self.assertEqual(evaluate('-5+2'), Decimal(-3))
    def test_division(self): self.assertEqual(format_number(evaluate('1/8')), '0.125')
    def test_zero(self):
        with self.assertRaises(CalculatorError): evaluate('1/0')
    def test_block_calls(self):
        with self.assertRaises(CalculatorError): evaluate('__import__("os").system("whoami")')
    def test_block_power(self):
        with self.assertRaises(CalculatorError): evaluate('2**999999')
    def test_block_attribute(self):
        with self.assertRaises(CalculatorError): evaluate('1 .real')
    def test_reject_big(self):
        with self.assertRaises(CalculatorError): evaluate('9'*161)
    def test_format(self): self.assertEqual(format_number(Decimal('25.0000')), '25')
if __name__ == '__main__': unittest.main()
