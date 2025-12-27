from typing import List
from .. import __version__

def cmd_version(argv: List[str]) -> int:
    print(__version__)
    return 0