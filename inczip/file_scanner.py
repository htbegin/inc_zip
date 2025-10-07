import os
import zlib
import datetime
from pathlib import Path
from typing import Dict
from concurrent.futures import ProcessPoolExecutor

from .models import FileMetadata

def _calculate_crc(file_path: Path) -> int:
    """Reads a file chunk by chunk and calculates its CRC32 checksum."""
    crc = 0
    with open(file_path, 'rb') as f:
        while chunk := f.read(65536):  # Read in 64k chunks
            crc = zlib.crc32(chunk, crc)
    return crc

def scan_directory(root_path: str, mode: str = 'fast') -> Dict[str, FileMetadata]:
    """
    Scans a directory recursively and returns a dictionary of FileMetadata
    objects for all files found, keyed by their relative path.

    In 'accurate' mode, the CRC is calculated for every file in parallel. 
    In 'fast' mode, the CRC is skipped (None).
    """
    metadata_map = {}
    root_path_obj = Path(root_path)

    # 1. First, quickly gather all file paths and their basic stats.
    file_entries = []
    for dirpath, _, filenames in os.walk(root_path_obj):
        for filename in filenames:
            absolute_path = Path(dirpath) / filename
            relative_path = absolute_path.relative_to(root_path_obj)
            
            # To handle platform-specific path separators (e.g., \ on Windows)
            relative_path_str = str(relative_path).replace('\\', '/')

            file_entries.append({
                "abs_path": absolute_path,
                "rel_path": relative_path_str,
                "stat": absolute_path.stat(),
            })

    # 2. Handle CRC calculation based on mode.
    if mode == 'accurate':
        paths_to_process = [entry["abs_path"] for entry in file_entries]
        with ProcessPoolExecutor() as executor:
            crc_results = executor.map(_calculate_crc, paths_to_process)

        # Combine results into the final map
        for entry, crc in zip(file_entries, crc_results):
            stat = entry["stat"]
            metadata = FileMetadata(
                path=entry["rel_path"],
                last_modified=datetime.datetime.fromtimestamp(stat.st_mtime),
                size=stat.st_size,
                crc=crc
            )
            metadata_map[metadata.path] = metadata
    else:  # fast mode
        for entry in file_entries:
            stat = entry["stat"]
            metadata = FileMetadata(
                path=entry["rel_path"],
                last_modified=datetime.datetime.fromtimestamp(stat.st_mtime),
                size=stat.st_size,
                crc=None
            )
            metadata_map[metadata.path] = metadata
            
    return metadata_map