
import zipfile
import datetime
from typing import Dict, List
import dataclasses

from .models import FileMetadata



def get_zip_metadata(zip_path: str) -> Dict[str, FileMetadata]:
    """
    Reads the central directory of a zip file and returns a dictionary of
    FileMetadata objects, keyed by the file path within the zip.
    """
    metadata_map = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for zip_info in zf.infolist():
            # Skip directories
            if zip_info.is_dir():
                continue

            # The timestamp is stored as a tuple: (year, month, day, hour, min, sec)
            dt_tuple = zip_info.date_time
            last_modified = datetime.datetime(*dt_tuple)

            metadata = FileMetadata(
                path=zip_info.filename,
                last_modified=last_modified,
                size=zip_info.file_size,
                crc=zip_info.CRC
            )
            metadata_map[metadata.path] = metadata
    return metadata_map

import json
from pathlib import Path

def create_zip(source_dir: str, files_to_add: List[FileMetadata], deleted_paths: List[str], output_path: str):
    """
    Creates a new zip archive containing the specified files to add and a manifest
    of deleted file paths.
    """
    source_root = Path(source_dir)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add the new/modified files
        for meta in files_to_add:
            absolute_path = source_root / meta.path
            zf.write(absolute_path, arcname=meta.path)

        # Create and add the manifest for deleted files
        if deleted_paths:
            manifest = {"deleted_files": deleted_paths}
            # Use zf.writestr to write in-memory data to the zip
            zf.writestr(".manifest.json", json.dumps(manifest, indent=4))

