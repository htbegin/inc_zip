import argparse
import sys
from typing import List, Optional

from .file_scanner import scan_directory
from .zip_utils import get_zip_metadata, create_zip
from .core import compare_states, Changes, restore_archive_chain

def create_parser():
    parser = argparse.ArgumentParser(description="A command-line tool for creating and restoring incremental zip backups.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Backup command parser
    backup_parser = subparsers.add_parser("backup", help="Create a new incremental backup.")
    backup_parser.add_argument("source_dir", help="The path to the source directory (the latest state).")
    backup_parser.add_argument("-b", "--base-zip", required=True, help="Path to the base (full) backup zip file.")
    backup_parser.add_argument("-o", "--output", required=True, help="Path for the new incremental zip file to be created.")
    backup_parser.add_argument("-i", "--increments", nargs='*', default=[], help="(Optional) Path to one or more existing incremental zips, in order of creation.")
    backup_parser.add_argument("--mode", choices=['fast', 'accurate'], default='fast', help="Comparison mode. Defaults to 'fast'.")

    # Restore command parser
    restore_parser = subparsers.add_parser("restore", help="Restore a directory from a backup chain.")
    restore_parser.add_argument("backup_files", nargs='+', help="The sequence of backup files to apply, in order.")
    restore_parser.add_argument("-d", "--destination", required=True, help="The destination directory to restore files to.")

    return parser

def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    # If argv is None, argparse uses sys.argv[1:]
    args = parser.parse_args(argv)

    try:
        if args.command == "backup":
            print("Starting backup...")
            # 1. Get metadata from old zips
            old_state = get_zip_metadata(args.base_zip)
            for inc_zip in args.increments:
                old_state.update(get_zip_metadata(inc_zip))

            # 2. Scan the new directory
            new_state = scan_directory(args.source_dir)

            # 3. Compare states
            changes = compare_states(old_state, new_state, mode=args.mode)

            # 4. Create the new zip
            files_to_add = changes.added + changes.modified
            deleted_paths = [meta.path for meta in changes.deleted]
            create_zip(args.source_dir, files_to_add, deleted_paths, args.output)
            
            print(f"Backup created at {args.output}")
            return 0
        elif args.command == "restore":
            print(f"Restoring from {len(args.backup_files)} archives to {args.destination}...")
            restore_archive_chain(args.backup_files, args.destination)
            print("Restore complete.")
            return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Should not be reached if subparsers are required
    return 1

def run_cli():
    sys.exit(main())

if __name__ == "__main__":
    run_cli()