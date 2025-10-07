"""Tests for the core logic."""
import datetime
import json
import tempfile
import zipfile
import zlib
from pathlib import Path

from inczip.core import Changes, compare_states, restore_archive_chain
from inczip.models import FileMetadata


# Helper to create dummy metadata
def create_meta(path, content, days_old=1):
    """Creates a FileMetadata object for testing."""
    return FileMetadata(
        path=path,
        last_modified=datetime.datetime.now() - datetime.timedelta(days=days_old),
        size=len(content),
        crc=zlib.crc32(content.encode())
    )


def test_compare_states():
    """
    Tests the comparison logic between an old state (zip) and a new state (fs).
    """
    # Define states
    old_state = {
        "file1.txt": create_meta("file1.txt", "content1"),
        "file_to_delete.txt": create_meta("file_to_delete.txt", "delete_me"),
        "file_to_modify.txt": create_meta("file_to_modify.txt", "original"),
    }

    new_state = {
        "file1.txt": create_meta("file1.txt", "content1"),  # Unchanged
        "file_to_modify.txt": create_meta(
            "file_to_modify.txt", "modified_content", days_old=0),
        "new_file.txt": create_meta("new_file.txt", "i am new", days_old=0),
    }

    # --- The actual test ---
    changes = compare_states(old_state, new_state, mode='accurate')

    # Assertions
    assert isinstance(changes, Changes)
    assert len(changes.added) == 1
    assert len(changes.modified) == 1
    assert len(changes.deleted) == 1

    assert "new_file.txt" in [meta.path for meta in changes.added]
    assert "file_to_modify.txt" in [meta.path for meta in changes.modified]
    assert "file_to_delete.txt" in [meta.path for meta in changes.deleted]


def test_restore_archive_chain():
    """
    Tests that the restore logic correctly extracts files and handles deletions.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "dest"
        base_zip_path = Path(temp_dir) / "base.zip"
        inc_zip_path = Path(temp_dir) / "inc.zip"

        # Create a base zip with two files
        with zipfile.ZipFile(base_zip_path, 'w') as zf:
            zf.writestr("file1.txt", "base_content_1")
            zf.writestr("file_to_delete.txt", "delete_me")

        # Create an incremental zip that modifies one file, adds another,
        # and deletes one.
        with zipfile.ZipFile(inc_zip_path, 'w') as zf:
            zf.writestr("file1.txt", "inc_content_1_modified")
            zf.writestr("new_file.txt", "new_content")
            manifest = {"deleted_files": ["file_to_delete.txt"]}
            zf.writestr(".manifest.json", json.dumps(manifest))

        # --- The actual test ---
        restore_archive_chain(
            [str(base_zip_path), str(inc_zip_path)], str(dest_path))

        # --- Assertions ---
        assert dest_path.exists()
        assert (dest_path / "file1.txt").read_text() == "inc_content_1_modified"
        assert (dest_path / "new_file.txt").read_text() == "new_content"
        assert not (dest_path / "file_to_delete.txt").exists()
