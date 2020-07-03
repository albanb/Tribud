#!/usr/bin/env python
# -*-coding:utf-8 -*
"""
The aim of this module is to serve data from the configuration file to other
 part of the application.
"""
import json
import os
import sys
import logging


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
