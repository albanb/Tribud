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


def decompose_path(path):
    """
    This function decompose the input path into its directory.

    Parameters
    ----------
    path: string
        The path to decompose

    Return
    ------
    list
        The list of directories composing the path. If the path is empty, the
        list will be empty.
    """
    drive_path = os.path.splitdrive(path)
    head, tail = os.path.split(drive_path[1])
    dirs = []
    while path != head:
        if tail != "":
            dirs.insert(0, tail)
        path = head
        head, tail = os.path.split(path)
    return dirs


class ConfigManager():
    """
    This class read the backup tool configuration and serve it to other
    modules.

    Parameters
    ----------
    arg1: string
        The path to the configuration file
    """

    def __init__(self, path):
        self.path = path
        self.logger = logging.getLogger("".join(["backups.", __name__]))
        try:
            config_file = open(self.path)
        except IOError:
            self.logger.critical(
                "Config file doesn't exist: %s", self.path)
            sys.exit()
        else:
            with config_file:
                try:
                    self.config = json.load(config_file)
                except json.decoder.JSONDecodeError:
                    self.logger.critical(
                        "Config file format not JSON compliant")
                    sys.exit()

    def _item_search(self, config_part, keys):
        if keys[0] not in config_part:
            self.logger.warning(
                "%s key not present in the config file", keys[0])
            return None
        if len(keys) == 1:
            return config_part[keys[0]]
        return self._item_search(config_part[keys[0]], keys[1:])

    def item_search(self, keys):
        """
        Look for a dedicated config inside the configuration file.

        Parameters:
        -----------
        Tuple
            A tuple containing the "path" to the nested configuration value.

        Return
        ------
        Variable
            The configuration value.
        """
        if keys[0] not in self.config:
            self.logger.warning(
                "%s key not present in the config file", keys[0])
            return None
        if len(keys) == 1:
            return self.config[keys[0]]
        return self._item_search(self.config[keys[0]], keys[1:])


class Container():
    """
    This class is the place to store the backups.

    Parameters:
    -----------
    arg1 : handler
        handler of the container used to backup data.
    """
    def __init__(self, handler):
        self.handler = handler

    def is_writeable(self):
        """
        This method check if the container exists and can be use to add
        data.
        """
        return self.handler.connected()

    def connect(self):
        """
        This method will ensure than the container exist and that connection
        with it is possible.
        """
        self.handler.create()

    def add(self, path):
        """
        This method is to add the data to the container.
        """
        self.handler.copy(path)


class DirHandler():
    """
    This class provide a handler for the container class to backup data in a
    simple directory.
    arg1 : string
        Path to the directory.
    """
    def __init__(self, path):
        self.bck_path = os.path.abspath(path)
        self.logger = logging.getLogger("".join(["backups.", __name__]))

    def is_writable(self):
        """
        Check if it is possible to write data in the directory.
        """
        return os.access(self.bck_path, os.W_OK)

    def connect(self):
        """
        Create the directory if it doesn't exist. The path shall be abs path.
        """
        if os.path.isabs(self.bck_path):
            os.makedirs(self.bck_path, exist_ok=True)
            self.logger.info("The backup directory is : %s", self.bck_path)
        else:
            self.logger.warning("%s is not an absolute path", self.bck_path)

    def add(self, path):
        """
        Add files recursively to the directory.
        The hierarchy of the source path is copy with the target path as root.

        Parameters:
        -----------
        String
            Path of the file or directory to copy.
            If it is a directory, the entire tree will be copied.
        """
        abs_path = os.path.abspath(path)
        if os.path.isfile(abs_path):
            base = os.path.split(abs_path)
            dirs = decompose_path(base[0])
        else:
            dirs = decompose_path(abs_path)
        target_path = self.bck_path
        for directory in dirs:
            target_path = os.path.join(target_path, directory)
        try:
            os.makedirs(target_path, exist_ok=True)
        except PermissionError:
            self.logger.warning(
                "The following directory can not be backup: %s",
                target_path)
            return 1
        try:
            shutil.copy2(abs_path, target_path)
        except IsADirectoryError:
            try:
                shutil.copytree(abs_path, target_path, dirs_exist_ok=True)
            except PermissionError:
                self.logger.warning(
                    "The following directory can not be copied: %s",
                    target_path)
                return 1
            except shutil.Error as err:
                for fail_copy in err.args:
                    self.logger.warning(
                        "The following file can not be copied: %s",
                        fail_copy[0])
                return 1
        except PermissionError:
            self.logger.warning(
                "The following file can not be copied: %s",
                target_path)
            return 1
        return 0


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(module)s : %(message)s',
        level=logging.DEBUG)
    test = ConfigManager(
        os.path.abspath(os.path.join(os.path.dirname(__file__),
                                     '../../tests/data/config.json')))
#        '../tests/data/config.json')))
    for key, value in test.item_search(('archive',)).items():
        print(key, ': ', value)
