"Core logic for comparing file states and restoring archives."
import json
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal

from .models import FileMetadata


@dataclass
class Changes:
    """Represents the changes between two states."""
    added: List[FileMetadata] = field(default_factory=list)
    modified: List[FileMetadata] = field(default_factory=list)
    deleted: List[FileMetadata] = field(default_factory=list)


CompareMode = Literal['fast', 'accurate']


def compare_states(old_state: Dict[str, FileMetadata],
                   new_state: Dict[str, FileMetadata],
                   mode: CompareMode = 'fast') -> Changes:
    """
    Compares an old and new metadata map and returns a Changes object.
    """
    changes = Changes()

    old_paths = set(old_state.keys())
    new_paths = set(new_state.keys())

    # Find added files
    for path in new_paths - old_paths:
        changes.added.append(new_state[path])

    # Find deleted files
    for path in old_paths - new_paths:
        changes.deleted.append(old_state[path])

    # Find potentially modified files
    for path in old_paths & new_paths:
        old_meta = old_state[path]
        new_meta = new_state[path]

        is_modified = False
        if old_meta.size != new_meta.size or \
           abs(int(old_meta.last_modified.timestamp()) -
               int(new_meta.last_modified.timestamp())) > 1:
            is_modified = True
        elif mode == 'accurate' and old_meta.crc != new_meta.crc:
            is_modified = True

        if is_modified:
            changes.modified.append(new_meta)

    return changes


def restore_archive_chain(archive_paths: List[str], destination: str):
    """
    Extracts a chain of zip archives to a destination and handles deletions
    as specified in .manifest.json files.
    """
    dest_path = Path(destination)
    os.makedirs(dest_path, exist_ok=True)

    all_deleted_files = set()

    # Extract all archives in order, overwriting older files with newer ones
    for archive_path in archive_paths:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # Check for a manifest and collect deleted files
            if ".manifest.json" in zf.namelist():
                with zf.open(".manifest.json") as mf:
                    manifest_data = json.load(mf)
                    for deleted_file in manifest_data.get("deleted_files", []):
                        all_deleted_files.add(deleted_file)

            # We need to extract all members except the manifest itself
            members_to_extract = [
                m for m in zf.infolist() if m.filename != ".manifest.json"]
            zf.extractall(dest_path, members=members_to_extract)

    # Process all deletions at the end
    for deleted_file in all_deleted_files:
        file_to_remove = dest_path / deleted_file
        # Use unlink with missing_ok=True to avoid errors if file was already gone
        file_to_remove.unlink(missing_ok=True)
