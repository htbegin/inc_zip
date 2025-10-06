
import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class FileMetadata:
    """A data class to hold metadata for a single file."""
    path: str
    last_modified: datetime.datetime
    size: int
    crc: int
