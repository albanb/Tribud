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
    This class read the backup tool configuration, which is json file, and
    serve it to other modules.

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

    def connected(self):
        """
        This method check if the container exists and can be use to add
        data.
        """
        return self.handler.is_writable()

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


class DirHandler():
    """
    This class provide a handler for the container class to backup data in a
    simple directory.
    arg1 : string
        Path to the destination directory.
    """
    def __init__(self, path):
        self.bckup_path = os.path.abspath(path)
        self.logger = logging.getLogger("".join(["backups.", __name__]))

    def is_writable(self):
        """
        Check if it is possible to write data in the directory.
        """
        return os.access(self.bckup_path, os.W_OK)

    def connect(self):
        """
        Create the directory if it doesn't exist. The path shall be abs path.
        """
        if os.path.isabs(self.bckup_path):
            os.makedirs(self.bckup_path, exist_ok=True)
            self.logger.info("The backup directory is : %s", self.bckup_path)
        else:
            self.logger.warning("%s is not an absolute path", self.bckup_path)

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
        src_path = os.path.abspath(path)
        dst_path = self.bckup_path
        if os.path.isfile(src_path):
            base = os.path.split(src_path)
            dirs = decompose_path(base[0])
        else:
            dirs = decompose_path(src_path)
        for directory in dirs:
            dst_path = os.path.join(dst_path, directory)
        self._copytree(src_path, dst_path)
        return 0

    def _copytree(self, src, dst):
        try:
            os.makedirs(dst, exist_ok=True)
        except PermissionError:
            self.logger.warning(
                "The following directory can not be backup: %s",
                dst)
            return 1
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            return 0
        with os.scandir(src) as itr:
            entries = list(itr)
        for srcentry in entries:
            srcname = os.path.join(src, srcentry.name)
            dstname = os.path.join(dst, srcentry.name)
            if srcentry.is_dir():
                self._copytree(srcname)
            else:
                shutil.copy2(srcname, dstname)
        return 0


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(module)s : %(message)s',
        level=logging.DEBUG)
    test = ConfigManager(
        os.path.abspath(os.path.join(os.path.dirname(__file__),
                                     '../../tests/data/config.json')))
# '../tests/data/config.json')))
    for key, value in test.item_search(('archive',)).items():
        print(key, ': ', value)
