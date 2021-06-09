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


def list_to_elt(function):
    """
    Decorator to transform argument list to call for each elements of the list.
    """

    def wrapper_list_to_elt(arg):
        if not isinstance(arg, list):
            return function(arg)
        return all((function(elt) for elt in arg))

    return wrapper_list_to_elt


@list_to_elt
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

    CHECK_OK = 1
    CHECK_NOK_TYPE = 2
    CHECK_NOK_PARENT = 3
    CHECK_NOK_SPECIFIC = 4

    def __init__(self, opt_parent, opt_key, opt_value):
        if not isinstance(opt_parent, tuple):
            self.option = (opt_key,)
        else:
            self.option = opt_parent + (opt_key,)
        self.value = opt_value
        self.checked = False

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
        self.checked = True
        if isinstance(self.value, option_definition[0]):
            if option_definition[1] == self.option[:-1]:
                if callable(option_definition[2]) and option_definition[2](self.value):
                    return ConfOpt.CHECK_OK
                return ConfOpt.CHECK_NOK_SPECIFIC
            return ConfOpt.CHECK_NOK_PARENT
        return ConfOpt.CHECK_NOK_TYPE


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
        try:
            config_file = open(self._path)
        except IOError as err:
            raise err
        else:
            with config_file:
                config = json.load(config_file)
        self._options = [
            ConfOpt(option[0], option[1], option[2]) for option in flatten(config)
        ]

    def sanitize(self, keys_definition):
        """
        This method will check all the options to send all non compliant configurations.

        # key: (mandatory, (type of key, (parent key), sanity function))
        :param keys_definition: dictionnary defining all options. Each item of the
        dictionnary shall have the following form:
        key: (boolean to define if key is mandatory or not,
              (type of key, (parent key), sanity function))
        :type keys_definition: dictionnary
        :returns: list of non compliant options, empty if all options are compliant.
        :rtype: list of tuple containing non compliant options path.
        """
        output = []
        for cle, valeur in keys_definition.items():
            option = self.get_key(valeur[1][1] + (cle,))
            if valeur[0] == 1 and option is None:
                output.append(valeur[1][1] + (cle,))
            if option is not None and option.check(valeur[1]) != ConfOpt.CHECK_OK:
                output.append(option.option)
        for opt in self._options:
            if opt.checked is False:
                output.append(opt.option)
        return output

    def get_key(self, key_name):
        """
        This method will look for key name in the configuration to retrieve the
        configuration definition.
        :param key_name: tuple containing the full path of the option
        :type key_name: tuple
        :returns: the configuration found, if any. None otherwise.
        :rtype: ConfOpt object
        """
        for option in self._options:
            if option.is_key(key_name):
                return option
        return None


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
        return self.handler.connect()

    def add(self, path):
        """
        This method is to add the data to the container.
        """
        return self.handler.add(path)


class DirHandler:
    """
    This class provide a handler for the container class to backup data in a
    directory of the filesystem.

    :param path: path to the backup directory.
    :type path: string

    """

    def __init__(self, path):
        self.bckup_dst = pathlib.Path(os.path.abspath(path))

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

        :return : name of the back up directory. None if connection not possible.
        :rtype: str
        """
        if self.bckup_dst.is_absolute():
            os.makedirs(self.bckup_dst, exist_ok=True)
            return str(self.bckup_dst)
        return None

    def add(self, path):
        """
        Add files of the path recursively to the backup directory.

        The full hierarchy of the source path, starting from root, is copied to the
        backup directory.

        :param path: path of the file or directory to copy
                  If it is a directory, the entire tree will be copied
        :type path: string
        :return : list of non backup files or directory
        :rtype: list
        """
        src_path = pathlib.Path(os.path.abspath(path))
        dst_path = self.bckup_dst
        dirs = src_path.parts[1:]
        if src_path.is_file():
            dirs = dirs[:-1]
        for directory in dirs:
            dst_path = dst_path.joinpath(directory)
        ret = self._copytree(src_path, dst_path)
        return ret

    def _copytree(self, src, dst):
        ret = []
        if (
            src.is_socket()
            or src.is_fifo()
            or src.is_block_device()
            or src.is_char_device()
        ):
            return ret.append(dst)
        if src.is_file() or src.is_symlink():
            try:
                os.makedirs(dst, exist_ok=True)
            except PermissionError:
                ret.append(dst)
            try:
                shutil.copy2(src, dst, follow_symlinks=False)
            except (FileExistsError, shutil.SameFileError, PermissionError):
                os.remove(dst.joinpath(src.name))
                shutil.copy2(src, dst, follow_symlinks=False)
        elif src.is_dir() and dst.exists():
            for child in src.iterdir():
                if child.is_file() or child.is_symlink():
                    shutil.copy2(child, dst, follow_symlinks=False)
                else:
                    self._copytree(child, dst.joinpath(child.name))
        elif src.is_dir and not dst.exists():
            try:
                shutil.copytree(src, dst, symlinks=True)
            except shutil.Error as err:
                for error in err.args[0]:
                    ret.append(error[0])
        else:
            return ret.append(dst)
        return ret


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s : %(levelname)s : %(module)s : %(message)s",
        level=logging.DEBUG,
    )
    try:
        test = ConfigManager(
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../docs/config.json")
            )
        )
    except (IOError, json.decoder.JSONDecodeError):
        sys.exit()
    CONFIG_KEYS_DEFINITION = {
        # key: (mandatory, (type of key, parent key, sanity function))
        "input": (1, (list, ("archive",), path_check)),
        "dir": (1, (str, ("archive", "output"), path_check)),
        "log": (0, (str, (), None)),
    }
    non_compliant_config = test.sanitize(CONFIG_KEYS_DEFINITION)
    print("config error:")
    for item in non_compliant_config:
        print(item)
    print("input:")
    print(test.get_key(("archive", "input")))
    print("output:")
    print(test.get_key(("archive", "output", "dir")))
    print("log:")
    print(test.get_key(("log",)))
