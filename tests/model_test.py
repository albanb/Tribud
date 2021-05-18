#!/bin/env python
# -*-coding:utf-8 -*
"""
Test of the config.py module.
"""
# pylint: disable=missing-function-docstring
# No need to add a docstring to each tests.

import os.path
import unittest
import shutil
import json
from context import model


class ConfOptTest(unittest.TestCase):
    """
    This class will test the ConfOpt class
    """

    def test_getvalue(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(option.get_value(), "/home/user")

    def test_iskey(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertTrue(option.is_key(("archive", "output", "dir")))

    def test_not_iskey(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertFalse(option.is_key(("archive", "output", "log")))

    def test_iskey_with_none(self):
        option = model.ConfOpt(None, "dir", "/home/user")
        self.assertTrue(option.is_key(("dir",)))

    def test_check(self):
        option = model.ConfOpt(None, "dir", "/home/user")
        self.assertTrue(option.check((str, (), model.path_check)))

    def test_check2(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(
            option.check((str, ("archive", "output"), model.path_check)), 1
        )

    def test_check_wrong_type(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(
            option.check((int, ("archive", "output"), model.path_check)), 2
        )

    def test_check_wrong_parent(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(option.check((str, ("archive", "input"), model.path_check)), 3)

    def test_check_wrong_parent2(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(option.check((str, (), model.path_check)), 3)

    def test_check_wrong_path(self):
        option = model.ConfOpt(("archive", "output"), "dir", "home/user")
        self.assertEqual(
            option.check((str, ("archive", "output"), model.path_check)), 4
        )


#  pylint: disable=too-many-instance-attributes
class ConfigTest(unittest.TestCase):
    """
    This class will test the Config class.
    """

    def setUp(self):
        self.path1 = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "data/config.json")
        )
        os.makedirs(os.path.dirname(self.path1), exist_ok=True)
        with open(self.path1, "w") as filep:
            filep.write(
                '{"archive":{"input": ["/home/alban/dev/soft/tribud/tests/data/config.json", "/home/alban/dev/soft/tribud/tests/data/test"], "output": "/home/alban/dev/soft/tribud/tests/data/tar"}}'
            )
        self.mandatory_keys = (("archive", "input"), ("archive", "output"))
        self.allowed_keys_ok = {
            # key: (type of key, parent key, sanity function)
            "archive": (dict, None, "dict"),
            "input": (str, "archive", "path"),
            "output": (str, "archive", "path"),
        }
        self.allowed_keys_bad_type = {
            # key: (type of key, parent key, sanity function)
            "archive": (dict, None, "dict"),
            "input": (str, "archive", "path"),
            "output": (dict, "archive", "path"),
        }
        self.allowed_keys_bad_parent = {
            # key: (type of key, parent key, sanity function)
            "archive": (dict, None, "dict"),
            "input": (str, None, "path"),
            "output": (dict, "archive", "path"),
        }
        self.path2 = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "data/config2.json")
        )
        with open(self.path2, "w") as filep:
            filep.write('{"archive": "data/config.json", "output": "data/tar"}')
        self.mandatory_keys2 = (("archive",), ("output",))
        self.path3 = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "data/config3.json")
        )
        with open(self.path3, "w") as filep:
            filep.write(
                '{"archive: ["data/config.json", "data/test"], "output": "data/tar"}'
            )

    def test_item_search_archive(self):
        json_config = model.ConfigManager(self.path1, self.mandatory_keys)
        result = json_config.item_search(("archive",))
        self.assertDictEqual(
            result,
            {
                "input": [
                    "/home/alban/dev/soft/tribud/tests/data/config.json",
                    "/home/alban/dev/soft/tribud/tests/data/test",
                ],
                "output": "/home/alban/dev/soft/tribud/tests/data/tar",
            },
        )

    def test_item_search_input(self):
        json_config = model.ConfigManager(self.path1, self.mandatory_keys)
        result = json_config.item_search(("archive", "input"))
        self.assertEqual(
            result,
            [
                "/home/alban/dev/soft/tribud/tests/data/config.json",
                "/home/alban/dev/soft/tribud/tests/data/test",
            ],
        )

    def test_item_search_output(self):
        json_config = model.ConfigManager(self.path1, self.mandatory_keys)
        result = json_config.item_search(("archive", "output"))
        self.assertEqual(result, "/home/alban/dev/soft/tribud/tests/data/tar")

    def test_item_search_log_not_exist(self):
        json_config = model.ConfigManager(self.path1, self.mandatory_keys)
        result = json_config.item_search(("log",))
        self.assertIsNone(result)

    def test_item_search_input_not_exist(self):
        self.assertRaises(
            KeyError, model.ConfigManager, self.path2, self.mandatory_keys
        )

    def test_invalid_json(self):
        self.assertRaises(
            json.decoder.JSONDecodeError,
            model.ConfigManager,
            self.path3,
            self.mandatory_keys,
        )

    def test_sanitize_ok(self):
        json_config = model.ConfigManager(self.path1, self.mandatory_keys)
        self.assertTrue(json_config.sanitize(self.allowed_keys_ok))

    def test_sanitize_bad_type(self):
        json_config = model.ConfigManager(self.path1, self.mandatory_keys)
        self.assertRaises(ValueError, json_config.sanitize, self.allowed_keys_bad_type)

    def test_sanitize_bad_parent(self):
        json_config = model.ConfigManager(self.path1, self.mandatory_keys)
        self.assertRaises(KeyError, json_config.sanitize, self.allowed_keys_bad_parent)

    def test_sanitize_relative_path(self):
        json_config = model.ConfigManager(self.path2, self.mandatory_keys2)
        self.assertRaises(ValueError, json_config.sanitize, self.allowed_keys_ok)

    def tearDown(self):
        os.remove(self.path1)
        os.remove(self.path2)
        os.remove(self.path3)


class DirHandlerTest(unittest.TestCase):
    """
    This class will test the DirHandler class.
    """

    def setUp(self):
        self.basepath = os.path.abspath(os.path.dirname(__file__))
        self.path1 = os.path.join(self.basepath, "test1")
        self.path2 = os.path.join(self.basepath, "test2")
        os.mkdir(self.path2)
        shutil.copy(__file__, self.path2)
        shutil.copy(os.path.join(self.basepath, "context.py"), self.path2)
        self.symlink_path = os.path.join(self.basepath, "test2/symlink_to_file")
        os.symlink(
            os.path.join(self.path2, "context.py"),
            self.symlink_path,
        )
        os.symlink(
            os.path.join(self.basepath, "../tribud"),
            os.path.join(self.basepath, "test2/symlink_to_directory"),
        )
        os.symlink(
            os.path.join(self.basepath, "test2"),
            os.path.join(self.basepath, "test2/recursive_symlink"),
        )

    def test_connect(self):
        directory = model.DirHandler(self.path1)
        directory.connect()
        self.assertTrue(os.access(self.path1, os.F_OK))

    def test_is_connected(self):
        directory = model.DirHandler(self.path2)
        self.assertTrue(directory.is_connected())

    def test_add_file(self):
        directory = model.DirHandler(self.path1)
        directory.connect()
        directory.add(os.path.abspath(__file__))
        self.assertTrue(
            os.path.isfile("".join([self.path1, os.path.abspath(__file__)]))
        )

    def test_add_symlink_file(self):
        directory = model.DirHandler(self.path1)
        directory.connect()
        directory.add(os.path.abspath(self.symlink_path))
        self.assertTrue(
            os.path.isfile("".join([self.path1, os.path.abspath(self.symlink_path)]))
            and os.path.islink(
                "".join([self.path1, os.path.abspath(self.symlink_path)])
            )
        )

    def test_add_directory(self):
        directory = model.DirHandler(self.path1)
        directory.connect()
        directory.add(os.path.abspath(self.path2))
        self.assertEqual(
            os.listdir("".join([self.path1, self.path2])).sort(),
            [
                "symlink_to_file",
                "context.py",
                "model_test.py",
                "symlink_to_directory",
                "recursive_symlink",
            ].sort(),
        )

    def tearDown(self):
        try:
            shutil.rmtree(self.path1)
        except FileNotFoundError:
            pass
        try:
            shutil.rmtree(self.path2)
        except FileNotFoundError:
            pass


def suite_confopt_test():
    """
    List of tests to run to test ConfOpt class.
    """
    tests = [
        "test_getvalue",
        "test_iskey",
        "test_not_iskey",
        "test_iskey_with_none",
        "test_check",
        "test_check2",
        "test_check_wrong_type",
        "test_check_wrong_parent",
        "test_check_wrong_parent2",
        "test_check_wrong_path",
    ]
    return unittest.TestSuite(map(ConfOptTest, tests))


def suite_config_test():
    """
    List of tests to run to test Config class.
    """
    tests = [
        "test_item_search_archive",
        "test_item_search_input",
        "test_item_search_output",
        "test_item_search_log_not_exist",
        "test_item_search_input_not_exist",
        "test_invalid_json",
        "test_sanitize_ok",
        "test_sanitize_bad_type",
        "test_sanitize_bad_parent",
        "test_sanitize_relative_path",
    ]
    return unittest.TestSuite(map(ConfigTest, tests))


def suite_dirhandler_test():
    """
    List of tests to run to test DirHandler class.
    """
    tests = [
        "test_connect",
        "test_is_connected",
        "test_add_file",
        "test_add_symlink_file",
        "test_add_directory",
    ]
    return unittest.TestSuite(map(DirHandlerTest, tests))


if __name__ == "__main__":
    # unittest.TextTestRunner(verbosity=2).run(suite_config_test())
    unittest.TextTestRunner(verbosity=2).run(suite_confopt_test())
    unittest.TextTestRunner(verbosity=2).run(suite_dirhandler_test())
