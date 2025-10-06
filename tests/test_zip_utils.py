
import zipfile
import tempfile
import os
from pathlib import Path
import datetime

from inczip.models import FileMetadata


# This import will fail initially, which is part of the TDD process.
from inczip.zip_utils import get_zip_metadata, create_zip

def test_get_zip_metadata():
    """
    Tests that get_zip_metadata correctly reads metadata from a zip file.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "test.zip"
        file1_path = Path(temp_dir) / "file1.txt"
        file2_path = Path(temp_dir) / "subdir" / "file2.txt"

        # Create dummy files
        os.makedirs(file2_path.parent)
        file1_path.write_text("content1")
        file2_path.write_text("content2")

        # Create a dummy zip file
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(file1_path, arcname="file1.txt")
            zf.write(file2_path, arcname="subdir/file2.txt")

        # --- The actual test ---
        metadata = get_zip_metadata(str(zip_path))

        # Assertions
        assert len(metadata) == 2
        assert "file1.txt" in metadata
        assert "subdir/file2.txt" in metadata

        file1_info = metadata["file1.txt"]
        assert file1_info.path == "file1.txt"
        assert file1_info.size == len("content1")
        
        # ZipFile stores timestamps in DOS format (2-second precision)
        # We check if the timestamp is approximately correct.
        file1_stat = file1_path.stat()
        dt_obj = datetime.datetime.fromtimestamp(file1_stat.st_mtime)
        # Python 3.8+ zipfile uses system timezone info, older versions might not
        # This makes direct comparison tricky, so we check for close enough
        assert abs(file1_info.last_modified - dt_obj).total_seconds() < 2

        # We can check CRC, but it requires reading the file.
        # For this initial test, we'll trust zipfile to get it right.
        assert isinstance(file1_info.crc, int)


def test_create_zip():
    """
    Tests that create_zip correctly creates an archive with specified files
    and a manifest of deleted files.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / "source"
        output_path = Path(temp_dir) / "output.zip"
        
        # Create dummy source files
        file_to_add_path = source_path / "added.txt"
        file_to_ignore_path = source_path / "ignored.txt"
        os.makedirs(source_path)
        file_to_add_path.write_text("add this content")
        file_to_ignore_path.write_text("ignore this")

        # Define what to add and what was deleted
        meta_to_add = FileMetadata(
            path="added.txt",
            last_modified=datetime.datetime.fromtimestamp(file_to_add_path.stat().st_mtime),
            size=len("add this content"),
            crc=0 # CRC not needed for this test's logic
        )
        deleted_paths = ["deleted1.txt", "subdir/deleted2.txt"]

        # --- The actual test ---
        create_zip(str(source_path), [meta_to_add], deleted_paths, str(output_path))

        # --- Assertions ---
        assert output_path.exists()

        with zipfile.ZipFile(output_path, 'r') as zf:
            # Check that the correct files are in the zip
            archived_files = zf.namelist()
            assert "added.txt" in archived_files
            assert ".manifest.json" in archived_files
            assert "ignored.txt" not in archived_files
            assert len(archived_files) == 2

            # Check the content of the added file
            with zf.open("added.txt") as f:
                content = f.read()
                assert content == b"add this content"

            # Check the content of the manifest
            with zf.open(".manifest.json") as f:
                import json
                manifest_data = json.load(f)
                assert manifest_data["deleted_files"] == deleted_paths

