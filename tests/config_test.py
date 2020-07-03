#!/bin/env python
# -*-coding:utf-8 -*
"""
Test of the config.py module.
"""
# pylint: disable=missing-function-docstring
# No need to add a docstring to each tests.

import os.path
import unittest
from context import config


class ConfigTest(unittest.TestCase):
    """
    This class will test the Config class.
    """

    def setUp(self):
        self.path1 = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  "data/config.json"))
        os.makedirs(os.path.dirname(self.path1), exist_ok=True)
        with open(self.path1, "w") as filep:
            filep.write(
                "{\"archive\":{\"input\": [\"data/config.json\",\
\"data/test\"], \"output\": \"data/tar\"}}")
        self.path2 = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  "data/config2.json"))
        with open(self.path2, "w") as filep:
            filep.write(
                "{\"former\": [\"data/config.json\",\
\"data/test\"], \"output\": \"data/tar\"}")

    def test_item_search_archive(self):
        json_config = config.ConfigManager(self.path1)
        result = json_config.item_search(("archive",))
        self.assertEqual(result, {'input': ['data/config.json',
                                            'data/test'],
                                  'output': 'data/tar'})

    def test_item_search_input(self):
        json_config = config.ConfigManager(self.path1)
        result = json_config.item_search(("archive", "input"))
        self.assertEqual(result, ['data/config.json',
                                  'data/test'])

    def test_item_search_output(self):
        json_config = config.ConfigManager(self.path1)
        result = json_config.item_search(("archive", "output"))
        self.assertEqual(result, 'data/tar')

    def test_item_search_archive_not_exist(self):
        json_config = config.ConfigManager(self.path2)
        result = json_config.item_search(("archive",))
        self.assertEqual(result, None)

    def test_item_search_input_not_exist(self):
        json_config = config.ConfigManager(self.path2)
        result = json_config.item_search(("archive", "input"))
        self.assertEqual(result, None)

    def tearDown(self):
        os.remove(self.path1)
        os.remove(self.path2)


def suite_config_test():
    """
    List of tests to run in the module
    """
    tests = ['test_item_search_archive',
             'test_item_search_input',
             'test_item_search_output',
             'test_item_search_archive_not_exist',
             'test_item_search_input_not_exist']
    return unittest.TestSuite(map(ConfigTest, tests))


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite_config_test())
