
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

from concurrent.futures import ProcessPoolExecutor

def _read_file_worker(path: Path) -> bytes:
    """Reads a file's content in a worker process."""
    return path.read_bytes()

def create_zip(source_dir: str, files_to_add: List[FileMetadata], deleted_paths: List[str], output_path: str, compress: bool = False):
    """
    Creates a new zip archive containing the specified files to add and a manifest
    of deleted file paths. File reading is done in parallel.
    """
    source_root = Path(source_dir)
    compression_method = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    
    paths_to_read = [source_root / meta.path for meta in files_to_add]
    arcnames = [meta.path for meta in files_to_add]

    with zipfile.ZipFile(output_path, 'w', compression_method) as zf:
        # Use a process pool to read files in parallel
        with ProcessPoolExecutor() as executor:
            # The map function returns an iterator that yields results in order
            contents_iterator = executor.map(_read_file_worker, paths_to_read)
            
            # Write the contents to the zip file in the main process
            for meta, content in zip(files_to_add, contents_iterator):
                info = zipfile.ZipInfo(meta.path, date_time=meta.last_modified.timetuple()[:6])
                # The compression type is already set on the ZipFile object, but we also
                # set it on the ZipInfo object for clarity and correctness.
                info.compress_type = compression_method
                zf.writestr(info, content)

        # Create and add the manifest for deleted files
        if deleted_paths:
            manifest = {"deleted_files": deleted_paths}
            zf.writestr(".manifest.json", json.dumps(manifest, indent=4))

