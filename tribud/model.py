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
            self.logger.warning("%s key not present in the config file", keys[0])
            return None
        if len(keys) == 1:
            return self.config[keys[0]]
        return self._item_search(self.config[keys[0]], keys[1:])


class Container:
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


class DirHandler:
    """
    This class provide a handler for the container class to backup data in a
    simple directory.
    arg1 : string
        Path to the destination directory.
    """

    def __init__(self, path):
        self.bckup_dst = pathlib.Path(os.path.abspath(path))
        self.logger = logging.getLogger("".join(["backups.", __name__]))

    def is_writable(self):
        """
        Check if it is possible to write data in the directory.
        """
        return os.access(self.bckup_dst, os.W_OK)

    def connect(self):
        """
        Create the directory if it doesn't exist. The path shall be abs path.
        """
        if self.bckup_dst.is_absolute():
            os.makedirs(self.bckup_dst, exist_ok=True)
            self.logger.info("The backup directory is : %s", str(self.bckup_dst))
        else:
            self.logger.warning("%s is not an absolute path", str(self.bckup_dst))

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
        src_path = pathlib.Path(path).resolve()
        dst_path = pathlib.Path(self.bckup_dst)
        dirs = src_path.parts[1:]
        if src_path.is_file():
            dirs = dirs[:-1]
        for directory in dirs:
            dst_path = dst_path.joinpath(directory)
        self._copytree(src_path, dst_path)
        return 0

    def _copytree(self, src, dst):
        if src.is_file():
            try:
                os.makedirs(dst, exist_ok=True)
            except PermissionError:
                self.logger.warning("The following directory can not be backup: %s", dst)
                return 1
            shutil.copy2(src, dst)
        elif dst.exists():
            for child in src.iterdir():
                if child.is_file():
                    shutil.copy2(child, dst)
                else:
                    self._copytree(child, dst.joinpath(child.name))
        else:
            shutil.copytree(src, dst)
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
