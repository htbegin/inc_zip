
from unittest.mock import patch, MagicMock

# This import will fail initially
from inczip.cli import main

# We patch the functions that the CLI is supposed to call.
# This allows us to test the CLI logic in isolation.
@patch('inczip.cli.get_zip_metadata', return_value={}) 
@patch('inczip.cli.scan_directory', return_value={})
@patch('inczip.cli.compare_states', return_value=MagicMock(added=[], modified=[], deleted=[]))
@patch('inczip.cli.create_zip') # This function doesn't exist yet
def test_backup_command_happy_path(mock_create_zip, mock_compare, mock_scan, mock_get_meta):
    """
    Tests that the backup command correctly parses args and calls the core logic.
    """
    # Simulate command line arguments
    args = [
        'backup',
        'test_source_dir',
        '--base-zip', 'base.zip',
        '--output', 'inc_1.zip',
        '--increments', 'inc_0.zip'
    ]

    # Run the main CLI function with the mocked arguments
    result = main(args)

    # Assertions
    assert result == 0 # Successful exit code

    # Check that our core logic functions were called with the correct args
    assert mock_get_meta.call_count == 2
    mock_scan.assert_called_once_with('test_source_dir')
    mock_compare.assert_called_once_with({}, {}, mode='fast')
    
    # Check that the final zip creation function is called correctly
    mock_create_zip.assert_called_once()
    create_zip_args = mock_create_zip.call_args[0]
    assert create_zip_args[0] == 'test_source_dir'
    
    
    @patch('inczip.cli.restore_archive_chain')
    def test_restore_command_happy_path(mock_restore):
        """
        Tests that the restore command correctly parses args and calls the core logic.
        """
        args = [
            'restore',
            '--destination', 'restore_dir',
            'base.zip',
            'inc_1.zip'
        ]
    
        result = main(args)
    
        assert result == 0
        mock_restore.assert_called_once_with(['base.zip', 'inc_1.zip'], 'restore_dir')
    
