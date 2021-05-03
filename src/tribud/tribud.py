#!/usr/bin/env python
# -*-coding:utf-8 -*
"""
A backup tool to save files on a local or remote dedicated location.
"""

import os.path
import logging
import appdirs

if __package__ == "":
    import model  # pylint: disable=import-error
    __appname__ = "tribud"
else:
    from tribud import model, __appname__   # pylint: disable=import-self


CONFIG_FILE = "config.json"


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
    logger = logging.getLogger("backups")
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
    tribudconfig = model.ConfigManager(confpath)
    bckdir = tribudconfig.item_search(("archive", "output"))
    toarchive = tribudconfig.item_search(("archive", "input"))
    handler = model.DirHandler(bckdir)
    backup = model.Container(handler)
    backup.connect()
    for files in toarchive:
        backup.add(files)
    return 0


# ---------- Main--------------------
if __name__ == "__main__":
    main()
