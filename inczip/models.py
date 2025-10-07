"""Data models for the incremental zip tool."""
import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class FileMetadata:
    """A data class to hold metadata for a single file."""
    path: str
    last_modified: datetime.datetime
    size: int
    crc: Optional[int] = None
