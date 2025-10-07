
from unittest.mock import patch, MagicMock

from inczip.cli import main, _get_all_zip_metadata
from inczip.file_scanner import scan_directory

# We patch the functions that the CLI is supposed to call.
# This allows us to test the CLI logic in isolation.
from concurrent.futures import Future

@patch('inczip.cli.create_zip')
@patch('inczip.cli.compare_states')
@patch('inczip.cli.ProcessPoolExecutor')
def test_backup_command_happy_path(mock_executor_cls, mock_compare, mock_create_zip):
    """
    Tests that the backup command correctly calls the core logic, mocking the parallel execution.
    """
    # Arrange: Set up mock return values for the futures
    mock_scan_result = {'new_file.txt': 'new_meta'}
    mock_zip_result = {'old_file.txt': 'old_meta'}
    mock_compare.return_value = MagicMock(added=[], modified=[], deleted=[])

    # Arrange: Mock the executor to return futures with our predefined results
    mock_executor_instance = mock_executor_cls.return_value.__enter__.return_value
    
    scan_future = Future()
    scan_future.set_result(mock_scan_result)
    
    zip_future = Future()
    zip_future.set_result(mock_zip_result)

    # The first submit call is for scan_directory, the second is for _get_all_zip_metadata
    mock_executor_instance.submit.side_effect = [scan_future, zip_future]

    # Act: Simulate command line arguments and run the main function
    args = [
        'backup',
        'test_source_dir',
        '--base-zip', 'base.zip',
        '--output', 'inc_1.zip',
        '--increments', 'inc_0.zip'
    ]
    result = main(args)

    # Assert
    assert result == 0
    mock_executor_instance.submit.assert_any_call(scan_directory, 'test_source_dir', mode='fast')
    mock_executor_instance.submit.assert_any_call(_get_all_zip_metadata, ['base.zip', 'inc_0.zip'])
    mock_compare.assert_called_once_with(mock_zip_result, mock_scan_result, mode='fast')
    mock_create_zip.assert_called_once()
    
    
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
    
