import gzip
from pathlib import Path


def agnostic_open(path, mode):
    path = Path(path)
    if path.suffix == '.gz':
        return gzip.open(path, mode)
    else:
        return open(path, mode)
