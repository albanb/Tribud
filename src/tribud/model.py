#!/usr/bin/env python
# -*-coding:utf-8 -*
"""
The aim of this module is to serve data from the configuration file to other
 part of the application.
"""
# pylint: disable=too-few-public-methods
import json
import os
import sys
import logging
import shutil
import pathlib


if __package__ == "" or __package__ is None:
    __appname__ = "tribud"


def path_check(path_to_check):
    """
    Check that the path given as a parameter is an valid absolute path.

    :param path_to_check: string which as to be checked
    :type path_to_check: str
    :return: True if it is a valid absolute path, False otherwise
    :rtype: boolean
    """
    path = pathlib.Path(path_to_check)
    if not path.is_absolute():
        return False
    return True


def flatten(dictio, output=None, parent=()):
    """
    Function to flatten a nested dictionnary.

    :param dictio: nested dictionnary to flatten
    :type dictio: dict
    :param output: list containing the flatten dictionnary. In the first call,
    the output should not be set as the flatten dictionnary is given as return.
    Each item of the list has the form: ((root, parent1, parent2...), last key, value)
    :type output: list
    :param parent: tuple containing the parent of the current key to be flatten
    :type parent: tuple
    :return: list containing the flatten dictionnary. each item of the list has
    the form: ((root, parent1, parent2...), last key, value)
    :rtype: list
    """
    if output is None:
        output = []
    for cle, valeur in dictio.items():
        if isinstance(valeur, dict):
            new_parent = parent + (cle,)
            flatten(valeur, output, new_parent)
        else:
            output.append((parent, cle, valeur))
    return output


class ConfOpt:
    """
    This class described one config options with its description to be able to check
    that the configuration option is compliant with its specification.

    :param opt_parent: parent option in the configuration file. None if no parent.
    :type opt_parent: list
    :param opt_key: configuration option store in this object.
    :type opt_key: str
    :param opt_value: associated value of the configuration option.
    :type opt_value: misc
    """

    def __init__(self, opt_parent, opt_key, opt_value):
        self.logger = logging.getLogger("".join([__appname__, ".", __name__]))
        if not isinstance(opt_parent, tuple):
            self.option = (opt_key,)
        else:
            self.option = opt_parent + (opt_key,)
        self.value = opt_value

    def get_value(self):
        """
        Get the value of this configuration option.

        :return: configuration option value
        :rtype: misc
        """
        return self.value

    def is_key(self, option):
        """
        Check if this option is the one given as parameter.

        :param option: option to be looking for
        :type option: tuple
        :return: True if this the configuration option, False otherwise
        :rtype: boolean
        """
        if option[:-1] == self.option[:-1] and option[-1] == self.option[-1]:
            return True
        return False

    def check(self, option_definition):
        """
        Check if the option is compliant with the definition given as a parameter.

        :param option_definition: definition of the configuration option to be check.
        The form of the definition is: (option type, parent, check function) with:
        option type: str, tuple, dict...
        parent: path to the option when nested in the configuration file as a tuple.
        If the option is at the first hierarchy level, an empty tuple shall be used.
        check function: callable to use to check the option. Existing functions are:
            - path_check: check that the option is a valid absolute path
        :type option_definition: tuple
        :return: 1 if option is valid, 2 if type is wrong, 3 if parent is wrong,
        4 if dedicated check is wrong
        :rtype: integer
        """
        if isinstance(self.value, option_definition[0]):
            if option_definition[1] == self.option[:-1]:
                if option_definition[2](self.value):
                    return 1
                return 4
            return 3
        return 2


class ConfigManager:
    """
    This class read the backup tool configuration, which is json file, and serve it to
    other modules.
    """

    def __init__(self, path):
        """
        :param path:  the path to the configuration file.
        :type path: string
        """

        self._path = path
        self._options = []
        self.logger = logging.getLogger("".join([__appname__, ".", __name__]))
        try:
            config_file = open(self._path)
        except IOError as err:
            self.logger.critical("Config file doesn't exist: %s", self._path)
            raise err
        else:
            with config_file:
                try:
                    config = json.load(config_file)
                except json.decoder.JSONDecodeError as err:
                    self.logger.critical("Config file format not JSON compliant")
                    raise err
        for option in flatten(config):
            self._options.append(ConfOpt(option[0], option[1], option[2]))

    def sanitize(self, keys_definition):
        """
        This method will check all the options to send all non compliant configurations.

        # key: (type of key, parent key, sanity function)
        :param keys_definition: dictionnary defining all options. Each item of the
        dictionnary shall have the following form:
        key: (boolean to define if key is mandatory or not,
              (type of key, parent key, sanity function))
        :type keys_definition: dictionnary
        :returns: True if options are compliant, False otherwise
        :rtype: boolean
        """
        pass


class _ConfOpt:
    """
    This class described one config options with its description to be able to check
    that the configuration option is compliant with its specification.

    :param opt_parent: parent option in the configuration file. None if no parent.
    :type opt_parent: str
    :param opt_key: configuration option store in this object.
    :type opt_key: str
    :param opt_value: associated value of the configuration option.
    :type opt_value: misc
    :param allowed: dict describing the allowed configuration option.
    :type allowed: dict
    """

    def __init__(self, opt_parent, opt_key, opt_value, allowed):
        self.logger = logging.getLogger("".join([__appname__, ".", __name__]))
        self.parent = opt_parent
        self.key = opt_key
        self.value = opt_value
        try:
            self.desc = allowed[opt_key]
        except KeyError as err:
            self.logger.critical(
                "%s is not allowed. Configuration file not valid", opt_key
            )
            raise err
        self.allowed = allowed

    def check(self):
        """
        Check one config option to ensure that it is a valid one.

        :return: True if option is valid, False if not
        :rtype: bool
        """
        if self.parent != self.desc[1]:
            self.logger.critical("%s option has not a valid parent.", self.key)
            raise KeyError("Key not valid, wrong parent.", self.key)
        if not isinstance(self.value, self.desc[0]):
            self.logger.critical(
                "The value of the option %s is not compliant with its type.", self.key
            )
            raise ValueError("Value type not expected.", self.key, self.desc[0])
        return self.confopt_dict()

    def confopt_dict(self):
        """
        This method check the validity of dict config option. It it is not a dict
        option, the option is pass through the next handler.

        :return: True if option is valid, False if not.
        :rtype: bool
        """
        if self.desc[2] == "dict":
            res = True
            for conf_key, conf_value in self.value.items():
                if isinstance(conf_value, list):
                    for element in conf_value:
                        conf_opt = _ConfOpt(self.key, conf_key, element, self.allowed)
                        res = conf_opt.check() and res
                else:
                    conf_opt = _ConfOpt(self.key, conf_key, conf_value, self.allowed)
                    res = conf_opt.check() and res
            return res
        return self.confopt_path()

    def confopt_path(self):
        """
        This method check the validity of path config option. It it is not a valid path
        option, the option is pass through the next handler.

        :return: True if option is valid, False if not.
        :rtype: bool
        """
        if self.desc[2] == "path":
            path = pathlib.Path(self.value)
            if not path.is_absolute():
                raise ValueError("This is not an absolute valid path.", self.key)
            return True
        return self.default_handler()

    def default_handler(self):
        """
        This method is the default option validity handler. If reach, it means that the
        option validity cannot be check, and a message is raised.

        :return: always return true as the option cannot be check.
        :rtype: bool
        """
        self.logger.warning(
            "The config option %s/%s content cannot be check.", self.parent, self.key
        )
        return True


class ConfigManagerb:
    """
    This class read the backup tool configuration, which is json file, and
    serve it to other modules.

    :param path: the path to the configuration file.
    :type path: string
    :param mandatory_keys: all mandatory keys that have to be in the config file.
    :type mandatory_keys: tuple
    """

    def __init__(self, path, mandatory_keys):
        self.path = path
        self.logger = logging.getLogger("".join([__appname__, ".", __name__]))
        try:
            config_file = open(self.path)
        except IOError as err:
            self.logger.critical("Config file doesn't exist: %s", self.path)
            raise err
        else:
            with config_file:
                try:
                    self.config = json.load(config_file)
                except json.decoder.JSONDecodeError as err:
                    self.logger.critical("Config file format not JSON compliant")
                    raise err
        for keys in mandatory_keys:
            if self.item_search(keys) is None:
                self.logger.critical(
                    "Mandatory keys %s not in the configuration file", keys
                )
                raise KeyError("Missing mandatory key in configuration file", keys)

    def sanitize(self, allowed_keys):
        """
        Check config file to ensure that all options are valid.

        :param allowed_keys: a dictionnary containing the description of all valid keys
        for the config file.
        :type keys: dict

        :return: config file valid or not.
        :rtype: boolean
        """
        res = True
        for conf_key, conf_value in self.config.items():
            if isinstance(conf_value, list):
                for element in conf_value:
                    conf_opt = _ConfOpt(None, conf_key, element, allowed_keys)
                    res = conf_opt.check() and res
            else:
                conf_opt = _ConfOpt(None, conf_key, conf_value, allowed_keys)
                res = conf_opt.check() and res
        return res

    def _item_search(self, config_part, keys):
        if keys[0] not in config_part:
            self.logger.warning("%s key not present in the config file", keys[0])
            return None
        if len(keys) == 1:
            return config_part[keys[0]]
        return self._item_search(config_part[keys[0]], keys[1:])

    def item_search(self, keys):
        """
        Look for a dedicated config inside the configuration file.

        :param keys: a tuple containing the "path" to the nested configuration value.
        :type keys: tuple

        :return: the configuration value.
        :rtype: variable
        """
        if keys[0] not in self.config:
            self.logger.warning("%s key not present in the config file", keys[0])
            return None
        if len(keys) == 1:
            return self.config[keys[0]]
        return self._item_search(self.config[keys[0]], keys[1:])


class Container:
    """
    This class is the handler to manage all possible backup location.

    The class behave as a proxy to concrete handler to perform the actual backup.
    Currently, only backup on the filesystem is managed.

    :param handler: concrete handler to use to backup data.

    :Example:

    >>>#Create the concrete handler to manage backup location
    >>>#Here it is a local filesystem directory
    >>>directory_handler = DirHandler("/path/to/backup/dir")
    >>>#Create the virtual handler to consistently manage backup location.
    >>>backup = Container(directory_handler)
    >>>#Connect to the container.
    >>>backup.connect()
    >>>#Check if the container is accessible and writeable
    >>>if backup.is_connected():
    >>>    print("Backup is possible")
    >>>else:
    >>>    print("Backup will not be done, the location
            is not accessible or not writable")
    >>>#Add file or directory to the backup location
    >>>backup.add("/file/to/save")

    """

    def __init__(self, handler):
        self.handler = handler

    def is_connected(self):
        """
        This method check if the container exists and can be use to add
        data.
        """
        return self.handler.is_connected()

    def connect(self):
        """
        This method will ensure than the container exist and that connection
        with it is possible.
        """
        self.handler.connect()

    def add(self, path):
        """
        This method is to add the data to the container.
        """
        self.handler.add(path)


class DirHandler:
    """
    This class provide a handler for the container class to backup data in a
    directory of the filesystem.

    :param path: path to the backup directory.
    :type path: string

    """

    def __init__(self, path):
        self.bckup_dst = pathlib.Path(os.path.abspath(path))
        self.logger = logging.getLogger("".join([__appname__, ".", __name__]))

    def is_connected(self):
        """
        Check if it is possible to write data in the directory.

        :return: indicate if it is possible to write in the DirHandler backup directory.
        :rtype: boolean
        """
        return os.access(self.bckup_dst, os.W_OK)

    def connect(self):
        """
        Create the backup directory if it doesn't exist. The path shall be abs path.
        """
        if self.bckup_dst.is_absolute():
            os.makedirs(self.bckup_dst, exist_ok=True)
            self.logger.info("The backup directory is : %s", str(self.bckup_dst))
        else:
            self.logger.warning("%s is not an absolute path", str(self.bckup_dst))

    def add(self, path):
        """
        Add files of the path recursively to the backup directory.

        The full hierarchy of the source path, starting from root, is copied to the
        backup directory.

        :param path: path of the file or directory to copy
                  If it is a directory, the entire tree will be copied
        :type path: string
        :return : full path of the backup file or directory
        :rtype: string
        """
        src_path = pathlib.Path(os.path.abspath(path))
        dst_path = pathlib.Path(self.bckup_dst)
        dirs = src_path.parts[1:]
        if src_path.is_file():
            dirs = dirs[:-1]
        for directory in dirs:
            dst_path = dst_path.joinpath(directory)
        self._copytree(src_path, dst_path)
        return dst_path

    def _copytree(self, src, dst):
        if src.is_file() or src.is_symlink():
            try:
                os.makedirs(dst, exist_ok=True)
            except PermissionError:
                self.logger.warning(
                    "The following directory can not be backup: %s", dst
                )
                return 1
            shutil.copy2(src, dst, follow_symlinks=False)
        elif dst.exists():
            for child in src.iterdir():
                if child.is_file() or child.is_symlink():
                    shutil.copy2(child, dst, follow_symlinks=False)
                else:
                    self._copytree(child, dst.joinpath(child.name))
        else:
            shutil.copytree(src, dst, symlinks=True)
        return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s : %(levelname)s : %(module)s : %(message)s",
        level=logging.DEBUG,
    )
    try:
        test = ConfigManager(
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../docs/config.json")
            ),
            (("archive", "input"), ("archive", "output")),
        )
    except (IOError, json.decoder.JSONDecodeError):
        sys.exit()

    CONFIG_KEYS_ALLOWED = {
        # key: (type of key, parent key, sanity function)
        "archive": (dict, None, "dict"),
        "input": (str, "archive", "path"),
        "output": (dict, "archive", "dict"),
        "dir": (str, "output", "path"),
        "log": (str, None, None),
    }
    try:
        print("sanitize: ", test.sanitize(CONFIG_KEYS_ALLOWED))
    except (KeyError, ValueError):
        sys.exit()
    for key, value in test.item_search(("archive",)).items():
        print(key, ": ", value)
