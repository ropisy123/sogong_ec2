import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ANSI 색상 코드
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

class ColorTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"{Colors.GREEN}✅ PASS: {test}{Colors.RESET}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f"{Colors.RED}❌ FAIL: {test}{Colors.RESET}")

    def addError(self, test, err):
        super().addError(test, err)
        print(f"{Colors.YELLOW}⚠️ ERROR: {test}{Colors.RESET}")

class ColorTestRunner(unittest.TextTestRunner):
    resultclass = ColorTestResult

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = ColorTestRunner(verbosity=2)
    runner.run(suite)
