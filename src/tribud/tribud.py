#!/usr/bin/env python
# -*-coding:utf-8 -*
"""
A backup tool to save files on a local or remote dedicated location.
"""

import os.path
import json
import sys
import logging
import appdirs

if __package__ == "":
    import model  # pylint: disable=import-error
    __appname__ = "tribud"
else:
    from tribud import model, __appname__  # pylint: disable=import-self


CONFIG_FILE = "config.json"
CONFIG_KEYS_DEFINITION = {
    "input": (1, (list, ("archive",), model.path_check)),
    "dir": (1, (str, ("archive", "output"), model.path_check)),
    "log": (1, (str, (), None)),
}


def application_path():
    """
    Create object to find main OS directory for config, data, cache... Use appdirs
    package.
    """
    return appdirs.AppDirs(__appname__)


def main():
    """
    Main entry point of the backup tool.
    """
    logger = logging.getLogger(__appname__)
    logger.setLevel(logging.DEBUG)
    fh = logging.StreamHandler()  # pylint: disable=invalid-name
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    app_dirs = application_path()
    confpath = os.path.join(app_dirs.user_config_dir, CONFIG_FILE)
    logger.info("Path to config: %s", confpath)
    try:
        tribudconfig = model.ConfigManager(confpath)
    except (IOError, json.decoder.JSONDecodeError):
        sys.exit()
    non_compliant_option = tribudconfig.sanitize(CONFIG_KEYS_DEFINITION)
    for item in non_compliant_option:
        logger.info("This option is not checked or not compliant: %s", item)
    bckdir = tribudconfig.get_key(("archive", "output", "dir"))
    toarchive = tribudconfig.get_key(("archive", "input"))
    handler = model.DirHandler(bckdir.value)
    backup = model.Container(handler)
    backup.connect()
    for files in toarchive.value:
        backup.add(files)
    return 0


# ---------- Main--------------------
if __name__ == "__main__":
    main()
