import unittest
from monitors.recursive_loop_detector import LoopDetector

class TestLoopDetector(unittest.TestCase):
    def test_loop_detection(self):
        detector = LoopDetector(threshold=2)
        code1 = "print('hello')"
        code2 = "print('world')"
        
        # Iteration 1
        self.assertFalse(detector.is_looping(code1))
        # Iteration 2
        self.assertFalse(detector.is_looping(code2))
        # Iteration 3 (Repeated code1)
        self.assertFalse(detector.is_looping(code1))
        # Iteration 4 (Repeated code1 again -> should trigger)
        self.assertTrue(detector.is_looping(code1))

    def test_whitespace_insensitivity(self):
        detector = LoopDetector(threshold=1)
        code1 = "print('hello')"
        code2 = "  print(  'hello'  )\n"
        
        self.assertFalse(detector.is_looping(code1))
        self.assertTrue(detector.is_looping(code2))

if __name__ == '__main__':
    unittest.main()
