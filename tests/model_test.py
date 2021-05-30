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


class UtilsTest(unittest.TestCase):
    """
    This class will test the model functions.
    """

    def test_flatten(self):
        dic = {"a": {"b": {"c": 1, "d": 2}}, "e": 3}
        self.assertEqual(
            model.flatten(dic),
            [(("a", "b"), "c", 1), (("a", "b"), "d", 2), ((), "e", 3)],
        )

    def test_path_check(self):
        self.assertTrue(model.path_check("/home/user"))

    def test_path_check_nok(self):
        self.assertFalse(model.path_check("home/user"))

    def test_path_check_list(self):
        self.assertTrue(model.path_check(["/home/user", "/var/log"]))

    def test_path_check_list_nok(self):
        self.assertFalse(model.path_check(["/home/user", "var/log"]))


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
        self.assertEqual(
            option.check((str, (), model.path_check)), model.ConfOpt.CHECK_OK
        )

    def test_check2(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(
            option.check((str, ("archive", "output"), model.path_check)),
            model.ConfOpt.CHECK_OK,
        )

    def test_check_list(self):
        option = model.ConfOpt(
            ("archive", "output"), "dir", ["/home/user", "/usr/var/toto"]
        )
        self.assertEqual(
            option.check((list, ("archive", "output"), model.path_check)),
            model.ConfOpt.CHECK_OK,
        )

    def test_check_wrong_type(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(
            option.check((int, ("archive", "output"), model.path_check)),
            model.ConfOpt.CHECK_NOK_TYPE,
        )

    def test_check_wrong_parent(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(
            option.check((str, ("archive", "input"), model.path_check)),
            model.ConfOpt.CHECK_NOK_PARENT,
        )

    def test_check_wrong_parent2(self):
        option = model.ConfOpt(("archive", "output"), "dir", "/home/user")
        self.assertEqual(
            option.check((str, (), model.path_check)), model.ConfOpt.CHECK_NOK_PARENT
        )

    def test_check_wrong_path(self):
        option = model.ConfOpt(("archive", "output"), "dir", "home/user")
        self.assertEqual(
            option.check((str, ("archive", "output"), model.path_check)),
            model.ConfOpt.CHECK_NOK_SPECIFIC,
        )

    def test_check_wrong_path_list(self):
        option = model.ConfOpt(
            ("archive", "output"), "dir", ["/home/user", "usr/var/toto"]
        )
        self.assertEqual(
            option.check((list, ("archive", "output"), model.path_check)),
            model.ConfOpt.CHECK_NOK_SPECIFIC,
        )

    def test_check_not_callable(self):
        option = model.ConfOpt(("archive", "output"), "dir", "home/user")
        self.assertEqual(
            option.check((str, ("archive", "output"), None)),
            model.ConfOpt.CHECK_NOK_SPECIFIC,
        )


class ConfigTest(unittest.TestCase):
    """
    This class will test the ConfigManager class.
    """

    def setUp(self):
        self.path1 = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "data/config.json")
        )
        os.makedirs(os.path.dirname(self.path1), exist_ok=True)
        with open(self.path1, "w") as filep:
            filep.write(
                '{"archive":{"input": ["/home/alban/config.json", "/home/alban/test"], "output": "/home/alban/tar"}}'
            )
        self.path2 = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "data/config2.json")
        )
        os.makedirs(os.path.dirname(self.path2), exist_ok=True)
        with open(self.path2, "w") as filep:
            filep.write('{"archive":{"input": ["home/config.json", "/home/test"]}}')
        self.path3 = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "data/config3.json")
        )
        with open(self.path3, "w") as filep:
            filep.write(
                '{"archive: ["data/config.json", "data/test"], "output": "data/tar"}'
            )

    def test_wrong_path(self):
        self.assertRaises(IOError, model.ConfigManager, "/test1/test2")

    def test_wrong_json(self):
        self.assertRaises(json.decoder.JSONDecodeError, model.ConfigManager, self.path3)

    def test_sanitize_ok(self):
        self.assertEqual(
            model.ConfigManager(self.path1).sanitize(
                {
                    "input": (1, (list, ("archive",), model.path_check)),
                    "output": (1, (str, ("archive",), model.path_check)),
                }
            ),
            [],
        )

    def test_sanitize_missing_mandatory_key(self):
        self.assertEqual(
            model.ConfigManager(self.path1).sanitize(
                {
                    "input": (1, (list, ("archive",), model.path_check)),
                    "output": (1, (str, ("archive",), model.path_check)),
                    "log": (1, (str, ("archive",), model.path_check)),
                }
            ),
            [{"log": (1, (str, ("archive",), model.path_check))}],
        )

    def test_sanitize_bad_parent(self):
        self.assertEqual(
            model.ConfigManager(self.path1).sanitize(
                {
                    "input": (0, (list, ("not_archive",), model.path_check)),
                    "output": (1, (str, ("archive",), model.path_check)),
                }
            ),
            [("archive", "input")],
        )

    def test_sanitize_bad_type(self):
        self.assertEqual(
            model.ConfigManager(self.path1).sanitize(
                {
                    "input": (1, (list, ("archive",), model.path_check)),
                    "output": (1, (int, ("archive",), model.path_check)),
                }
            ),
            [("archive", "output")],
        )

    def test_sanitize_bad_value(self):
        self.assertEqual(
            model.ConfigManager(self.path2).sanitize(
                {
                    "input": (1, (list, ("archive",), model.path_check)),
                }
            ), [("archive", "input")]
        )

    def test_sanitize_missing_key_check(self):
        self.assertEqual(
            model.ConfigManager(self.path1).sanitize(
                {
                    "input": (1, (list, ("archive",), model.path_check)),
                }
            ),
            [("archive", "output")],
        )

    def test_get_key(self):
        configuration = model.ConfigManager(self.path1).get_key(("archive", "input"))
        if configuration is None:
            self.assertIsNotNone(configuration)
        self.assertEqual(
            configuration.get_value(),
            ["/home/alban/config.json", "/home/alban/test"],
        )

    @unittest.skip("Not implemented yet")
    def test_get_key2(self):
        configuration = model.ConfigManager(self.path1).get_key(("input",))
        if configuration is None:
            self.assertIsNotNone(configuration)
        self.assertEqual(
            configuration.get_value(),
            ["/home/alban/config.json", "/home/alban/test"],
        )

    def test_get_no_key(self):
        configuration = model.ConfigManager(self.path1)
        self.assertIsNone(
            configuration.get_key(
                "log",
            )
        )

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


def suite_utilstest():
    """
    List of tests to run to test utility function in model.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(UtilsTest))
    return suite


def suite_confopt_test():
    """
    List of tests to run to test ConfOpt class.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(ConfOptTest))
    return suite


def suite_config_test():
    """
    List of tests to run to test the ConfigManager class.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(ConfigTest))
    return suite


def suite_dirhandler_test():
    """
    List of tests to run to test DirHandler class.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(DirHandlerTest))
    return suite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite_config_test())
    unittest.TextTestRunner(verbosity=2).run(suite_utilstest())
    unittest.TextTestRunner(verbosity=2).run(suite_confopt_test())
    unittest.TextTestRunner(verbosity=2).run(suite_dirhandler_test())
