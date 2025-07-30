"""
Test Runner for Backtrader Integration
======================================

This script runs all tests for the Backtrader integration.
"""
import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_all_tests():
    """Run all tests for the Backtrader integration."""
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests from all test modules
    test_modules = [
        'backtrader.tests.test_data_converter',
        'backtrader.tests.test_base_strategy',
        'backtrader.tests.test_scalping_strategy'
    ]
    
    for module_name in test_modules:
        try:
            # Load tests from the module
            module_suite = loader.loadTestsFromName(module_name)
            suite.addTests(module_suite)
            print(f"Loaded tests from {module_name}")
        except Exception as e:
            print(f"Failed to load tests from {module_name}: {e}")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)