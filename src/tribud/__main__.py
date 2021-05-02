"""
The entry point for the trivial back-up tool.
"""

import sys

if __package__ == "":
    from tribud import main
else:
    from tribud.tribud import main


sys.exit(main())
