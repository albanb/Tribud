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


class ConfigManager:
    """
    This class read the backup tool configuration, which is json file, and
    serve it to other modules.

    :param path: the path to the configuration file
    :type path: string
    """

    def __init__(self, path):
        self.path = path
        self.logger = logging.getLogger("".join(["backups.", __name__]))
        try:
            config_file = open(self.path)
        except IOError:
            self.logger.critical("Config file doesn't exist: %s", self.path)
            sys.exit()
        else:
            with config_file:
                try:
                    self.config = json.load(config_file)
                except json.decoder.JSONDecodeError:
                    self.logger.critical("Config file format not JSON compliant")
                    sys.exit()

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
        self.logger = logging.getLogger("".join(["backups.", __name__]))

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
    test = ConfigManager(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../tests/data/config.json")
        )
    )
    for key, value in test.item_search(("archive",)).items():
        print(key, ": ", value)
