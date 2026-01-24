import os
from pathlib import Path
from hashlib import md5
import pickle
from typing import TypeVar, Any

CACHE_DIR_PATH = os.environ.get("CACHE_DIR", "cache")
CACHE_DIR = Path(CACHE_DIR_PATH)

T = TypeVar('T')

class CacheError(Exception):
    """Raised when a cache operation fails."""
    pass

def _filename(key: str) -> Path:
    encoded = md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{encoded}.pkl"

def get(key: str) -> object | None:
    path = _filename(key)
    if path.is_file():
        with path.open("rb") as f:
            return pickle.load(f)
    return None

def set(key: str, obj: Any) -> None:
    path = _filename(key)
    try:
        with path.open("wb") as f:
            pickle.dump(obj, f)
    except (pickle.PickleError, OSError, IOError) as e:
        raise CacheError(f"Failed to cache '{key}': {e}") from e
