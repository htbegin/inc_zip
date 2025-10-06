# inczip: 增量ZIP备份工具

`inczip` 是一个基于Python的命令行工具，用于创建和恢复基于ZIP格式的增量备份。它适用于需要对大量文件进行版本化、可回溯备份的场景。

## 命令行界面 (CLI)

工具通过 `backup` 和 `restore` 两个子命令提供核心功能。

### 主命令 (`inczip --help`)

```text
usage: inczip [-h] {backup,restore} ...

A command-line tool for creating and restoring incremental zip backups.

positional arguments:
  {backup,restore}
    backup          Create a new incremental backup.
    restore         Restore a directory from a backup chain.

optional arguments:
  -h, --help          show this help message and exit
```

### `backup` 子命令 (`inczip backup --help`)

用于创建新的增量备份。它会将源目录与一个备份链（基础包+已有增量包）进行比较，并生成一个只包含变更内容的新增量包。

```text
usage: inczip backup [-h] -b BASE_ZIP [-i [INCREMENTS ...]] -o OUTPUT
                     [--mode {fast,accurate}] [--workers N]
                     [--exclude PATTERN]
                     source_dir

Create a new incremental backup by comparing a source directory against a backup chain.

positional arguments:
  source_dir            The path to the source directory (the latest state).

required arguments:
  -b BASE_ZIP, --base-zip BASE_ZIP
                        Path to the base (full) backup zip file.
  -o OUTPUT, --output OUTPUT
                        Path for the new incremental zip file to be created.

optional arguments:
  -h, --help            show this help message and exit
  -i [INCREMENTS ...], --increments [INCREMENTS ...]
                        (Optional) Path to one or more existing incremental
                        zips, in order of creation (inc_1.zip inc_2.zip ...).
  --mode {fast,accurate}
                        Comparison mode. Defaults to 'fast'.
                        'fast': Compares files based on modification time and
                        size. Much faster, but not 100% reliable if timestamps
                        are manipulated.
                        'accurate': If time/size match, performs a CRC-32 hash
                        comparison on file content. Slower but guarantees
                        accuracy.
  --workers N           Number of CPU cores to use for analysis and
                        compression. Defaults to all available cores. Use 1 to
                        disable parallel processing.
  --exclude PATTERN     (Optional, can be used multiple times) A glob pattern
                        for files/directories to exclude from the backup, e.g.,
                        '*.log' or 'tmp/'.
  -v, --verbose         Enable verbose output, showing progress and file
                        details.
```

### `restore` 子命令 (`inczip restore --help`)

用于从一个备份链（基础包和一系列增量包）中恢复文件到指定目录。

```text
usage: inczip restore [-h] -d DESTINATION [--workers N] [--force]
                      backup_files [backup_files ...]

Restore a directory by applying a full backup and a sequence of incremental backups.

positional arguments:
  backup_files          The sequence of backup files to apply, in order.
                        Must start with the base zip, followed by
                        incrementals (e.g., base.zip inc_1.zip inc_2.zip).

required arguments:
  -d DESTINATION, --destination DESTINATION
                        The destination directory to restore files to. It will
                        be created if it doesn't exist. WARNING: Contents may
                        be overwritten or deleted.

optional arguments:
  -h, --help            show this help message and exit
  --workers N           Number of CPU cores to use for decompression.
                        Defaults to all available cores.
  -f, --force           Bypass confirmation prompts before overwriting or
                        deleting files in the destination directory.
  -v, --verbose         Enable verbose output, showing files as they are
                        restored and deleted.
```
