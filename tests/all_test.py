#!/usr/bin/env python
# -*-coding:utf-8 -*
"""
Gather all tests for tribud.
"""
# pylint: disable=missing-function-docstring
# No need to add a docstring to each tests.

import sys
import unittest
import model_test

if __name__ == "__main__":
    suite1 = model_test.suite_utilstest()
    suite2 = model_test.suite_confopt_test()
    suite3 = model_test.suite_config_test()
    suite4 = model_test.suite_dirhandler_test()
    all_tests = unittest.TestSuite([suite1, suite2, suite3, suite4])
    result = unittest.TextTestRunner(verbosity=2).run(all_tests)
    sys.exit(not result.wasSuccessful())
