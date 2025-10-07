"""Command-line interface for the incremental zip tool."""
import argparse
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional

from .core import compare_states, restore_archive_chain
from .file_scanner import scan_directory
from .zip_utils import create_zip, get_zip_metadata


def create_parser():
    """Creates the argument parser for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="A command-line tool for creating and restoring incremental zip backups.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Backup command parser
    backup_parser = subparsers.add_parser(
        "backup", help="Create a new incremental backup.")
    backup_parser.add_argument(
        "source_dir", help="The path to the source directory (the latest state).")
    backup_parser.add_argument(
        "-b", "--base-zip", required=True, help="Path to the base (full) backup zip file.")
    backup_parser.add_argument(
        "-o", "--output", required=True,
        help="Path for the new incremental zip file to be created.")
    backup_parser.add_argument(
        "-i", "--increments", nargs='*', default=[],
        help="(Optional) Path to one or more existing incremental zips, in order of creation.")
    backup_parser.add_argument(
        "--mode", choices=['fast', 'accurate'], default='fast',
        help="Comparison mode. Defaults to 'fast'.")
    backup_parser.add_argument(
        "--compress", action='store_true',
        help="Enable DEFLATE compression for the zip archive.")

    # Restore command parser
    restore_parser = subparsers.add_parser(
        "restore", help="Restore a directory from a backup chain.")
    restore_parser.add_argument(
        "backup_files", nargs='+', help="The sequence of backup files to apply, in order.")
    restore_parser.add_argument(
        "-d", "--destination", required=True, help="The destination directory to restore files to.")

    return parser


def _get_all_zip_metadata(paths: List[str]) -> Dict[str, 'FileMetadata']:
    """Helper function to run in a process, gets metadata from a list of zips."""
    all_metadata = {}
    for path in paths:
        all_metadata.update(get_zip_metadata(path))
    return all_metadata


def main(argv: Optional[List[str]] = None) -> int:
    """The main entry point for the command-line interface."""
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "backup":
            print("Starting backup...")
            with ProcessPoolExecutor(max_workers=2) as executor:
                print(
                    "Scanning source directory and existing archives in parallel...")
                scan_future = executor.submit(
                    scan_directory, args.source_dir, mode=args.mode)
                zip_paths = [args.base_zip] + args.increments
                zip_future = executor.submit(_get_all_zip_metadata, zip_paths)
                new_state = scan_future.result()
                old_state = zip_future.result()

            print("Comparing states...")
            changes = compare_states(old_state, new_state, mode=args.mode)

            print("Creating new archive...")
            files_to_add = sorted(
                changes.added + changes.modified, key=lambda meta: meta.path)
            deleted_paths = sorted([meta.path for meta in changes.deleted])
            create_zip(args.source_dir, files_to_add,
                       deleted_paths, args.output, compress=args.compress)

            print(f"Backup created at {args.output}")
            return 0
        if args.command == "restore":
            print(
                f"Restoring from {len(args.backup_files)} archives to {args.destination}...")
            restore_archive_chain(args.backup_files, args.destination)
            print("Restore complete.")
            return 0
    except (IOError, ValueError, TypeError) as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return 1

    return 1


def run_cli():
    """Runs the command-line interface and exits with the appropriate status code."""
    sys.exit(main())


if __name__ == "__main__":
    run_cli()
