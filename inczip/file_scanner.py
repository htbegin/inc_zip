
import os
import zlib
import datetime
from pathlib import Path
from typing import Dict

from .models import FileMetadata

def _calculate_crc(file_path: Path) -> int:
    """Reads a file chunk by chunk and calculates its CRC32 checksum."""
    crc = 0
    with open(file_path, 'rb') as f:
        while chunk := f.read(65536):  # Read in 64k chunks
            crc = zlib.crc32(chunk, crc)
    return crc

def scan_directory(root_path: str) -> Dict[str, FileMetadata]:
    """
    Scans a directory recursively and returns a dictionary of FileMetadata
    objects for all files found, keyed by their relative path.
    """
    metadata_map = {}
    root_path_obj = Path(root_path)

    for dirpath, _, filenames in os.walk(root_path_obj):
        for filename in filenames:
            absolute_path = Path(dirpath) / filename
            relative_path = absolute_path.relative_to(root_path_obj)
            
            file_stat = absolute_path.stat()
            last_modified = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            
            # To handle platform-specific path separators (e.g., \ on Windows)
            relative_path_str = str(relative_path).replace('\\', '/')

            metadata = FileMetadata(
                path=relative_path_str,
                last_modified=last_modified,
                size=file_stat.st_size,
                crc=_calculate_crc(absolute_path)
            )
            metadata_map[metadata.path] = metadata
            
    return metadata_map
