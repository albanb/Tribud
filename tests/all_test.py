#!/usr/bin/env python
# -*-coding:utf-8 -*
"""
Gather all tests for tribud.
"""
# pylint: disable=missing-function-docstring
# No need to add a docstring to each tests.

import unittest
import config_test

if __name__ == '__main__':
    suite1 = config_test.suite_config_test()
    all_tests = unittest.TestSuite([suite1])
    unittest.TextTestRunner(verbosity=2).run(all_tests)
