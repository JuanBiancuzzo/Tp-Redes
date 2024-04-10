import unittest

class TestCodigo(unittest.TestCase):

    def test01(self):
        self.assertEqual(1 + 2, 3)

if __name__ == '__main__':
    unittest.main()
