
import tempfile
from pathlib import Path
import os

# This import will fail initially.
from inczip.file_scanner import scan_directory
from inczip.models import FileMetadata

def test_scan_directory():
    """
    Tests that scan_directory correctly scans a directory and returns metadata.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        root_path = Path(temp_dir)
        file1_path = root_path / "file1.txt"
        file2_path = root_path / "subdir" / "file2.txt"
        empty_dir_path = root_path / "empty_dir"

        # Create dummy files and directories
        os.makedirs(file2_path.parent)
        os.makedirs(empty_dir_path)
        file1_path.write_text("content1")
        file2_path.write_text("content2")

        # --- The actual test ---
        # We need to decide if scan_directory should calculate CRC, as it's slow.
        # For TDD, let's assume it does for now.
        metadata = scan_directory(str(root_path))

        # Assertions
        assert len(metadata) == 2
        assert "file1.txt" in metadata
        assert os.path.join("subdir", "file2.txt") in metadata

        file1_info = metadata["file1.txt"]
        assert isinstance(file1_info, FileMetadata)
        assert file1_info.path == "file1.txt"
        assert file1_info.size == len("content1")
