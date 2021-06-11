======
TRIBUD
======

.. image:: https://travis-ci.com/albanb/tribud.svg?branch=master
   :target: https://travis-ci.com/albanb/tribud

Tribud is a trivial back up manager. It aims at simply back-up normal files defined in the configuration. No complicated incremental back-up, partition cloning or time schedule. Just a tool to back-up the configured files and directory in a defined directory.
The configuration is done thanks to a json file.

Feature
-------
Able to manage one or more files or directory in a back-up directory.
Log non back-up file in the terminal.
Work on GNU/Linux and Windows.

Installing
----------
Download the zip.
Build the package::
 python -m build

Install it::
 pip install tribud-*version*-py3-none-any.whl

Configuration
-------------
The configuration is done through a JSON file. Its location is determined depending on the OS:
* On GNU/Linux, according to XDG specs, by default it is: /home/*user*/.config/tribud/config.json
* On Windows, by default: C:\\Users\\*user*\\AppData\\Local
