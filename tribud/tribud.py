#!/usr/bin/env python
# -*-coding:utf-8 -*
"""
A backup tool to save files on a local or remote dedicated location.
"""

import os.path
import logging
import model


def main():
    """
    Main entry point of the backup tool.
    """
    confpath = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '../tests/data/config.json'))
    logger.info("Path to config: %s", confpath)
    test = config.ConfigManager(confpath)
    for key, value in test.item_search(('archive',)).items():
        print(key, ': ', value)
    return 0


# ---------- Main--------------------
if __name__ == '__main__':
    logger = logging.getLogger('backups')
    logger.setLevel(logging.DEBUG)
    fh = logging.StreamHandler()
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    main()
