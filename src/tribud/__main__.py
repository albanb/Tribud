"""
The entry point for the trivial back-up tool.
"""

import sys

if __package__ == "":
    from tribud import main  # pylint: disable=no-name-in-module
else:
    from tribud.tribud import main


sys.exit(main())
