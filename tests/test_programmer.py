import unittest
from programmer import *
class TestProgrammer(unittest.TestCase):
    def test_bases(self):
        assert display(255, 8)=={'HEX':'FF','DEC':'-1','OCT':'377','BIN':'11111111'}
        assert display(10,16)['BIN'].endswith('1010')
    def test_parse(self):
        assert parse_value('FF','HEX',8)==255
        assert parse_value('1010','BIN',8)==10
        assert parse_value('-1','DEC',8)==255
    def test_bitwise(self):
        assert operate(0b1100,'AND',0b1010,8)==8
        assert operate(12,'OR',10,8)==14
        assert operate(12,'XOR',10,8)==6
        assert operate(0,'NOT',bits=8)==255
    def test_shifts(self):
        assert operate(1,'<<',3,8)==8
        assert operate(16,'>>',2,8)==4
        with self.assertRaises(ProgrammerError): operate(1,'<<',8,8)
    def test_bounds(self):
        assert operate(255,'+',1,8)==0
        assert operate(0,'-',1,8)==255
        assert operate(200,'*',2,8)==144
    def test_errors(self):
        with self.assertRaises(ProgrammerError): parse_value('2','BIN')
        with self.assertRaises(ProgrammerError): operate(1,'/',0,8)
        with self.assertRaises(ProgrammerError): operate(1,'???',1,8)
    def test_large_division(self):
        assert signed(operate(-(2**63),'/',1,64),64) == -(2**63)
        assert signed(operate(-(2**63),'/',3,64),64) == -(2**63)//3 + 1
    def test_division(self):
        assert signed(operate(-7,'/',2,8),8)==-3
        assert signed(operate(-7,'%',2,8),8)==1 # unsigned remainder explicitly
if __name__=='__main__': unittest.main()
