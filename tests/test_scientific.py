import unittest
from decimal import Decimal
from engine import CalculatorError, evaluate

class ScientificEngineTests(unittest.TestCase):
    def test_square(self): self.assertEqual(evaluate('3**2'), Decimal(9))
    def test_negative_power(self): self.assertEqual(evaluate('2**-3'), Decimal('0.125'))
    def test_factorial(self): self.assertEqual(evaluate('fact(5)'), Decimal(120))
    def test_inverse(self): self.assertEqual(evaluate('inv(4)'), Decimal('0.25'))
    def test_sqrt(self): self.assertEqual(evaluate('sqrt(81)'), Decimal(9))
    def test_log(self): self.assertEqual(evaluate('log(1000)'), Decimal(3))
    def test_ln(self): self.assertAlmostEqual(float(evaluate('ln(e)')), 1, places=13)
    def test_sin_degrees(self): self.assertAlmostEqual(float(evaluate('sin(30)')), 0.5, places=12)
    def test_cos_degrees(self): self.assertAlmostEqual(float(evaluate('cos(60)')), 0.5, places=12)
    def test_radians(self): self.assertAlmostEqual(float(evaluate('sin(pi/2)', 'RAD')), 1, places=12)
    def test_order(self): self.assertEqual(evaluate('2+3**2'), Decimal(11))
    def test_block_import(self):
        with self.assertRaises(CalculatorError): evaluate('__import__("os")')
    def test_reject_huge_power(self):
        with self.assertRaises(CalculatorError): evaluate('99**1000')
    def test_reject_fractional_power(self):
        with self.assertRaises(CalculatorError): evaluate('2**0.5')
    def test_reject_bad_factorial(self):
        with self.assertRaises(CalculatorError): evaluate('fact(-1)')
    def test_reject_tan_90(self):
        with self.assertRaises(CalculatorError): evaluate('tan(90)')
    def test_reject_other_methods(self):
        with self.assertRaises(CalculatorError): evaluate('pi.real')
    def test_reject_extra_arguments(self):
        with self.assertRaises(CalculatorError): evaluate('sin(1, 2)')

if __name__ == '__main__': unittest.main()
