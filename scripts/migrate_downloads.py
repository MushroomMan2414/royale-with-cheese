"""Copy a staged download volume without overwriting existing host files."""

import filecmp
import os
from pathlib import Path
import shutil
import sys


def migrate(source: Path, destination: Path) -> None:
    destination = destination.resolve()
    directories = []
    files = []
    for root, dirs, names in os.walk(source, followlinks=False):
        for name in dirs + names:
            path = Path(root) / name
            target = destination / path.relative_to(source)
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError(f"Unsupported item in old volume: {path}")
            if target.is_symlink() or not target.resolve().is_relative_to(destination):
                raise ValueError(f"Destination escapes downloads directory: {target}")
            if path.is_dir():
                if target.exists() and not target.is_dir():
                    raise ValueError(f"Destination is not a directory: {target}")
                directories.append(target)
            else:
                if target.exists() and (
                    not target.is_file() or not filecmp.cmp(path, target, shallow=False)
                ):
                    raise ValueError(f"Different file already exists: {target}")
                files.append((path, target))

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    for path, target in files:
        if not target.exists():
            with path.open("rb") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst)


if __name__ == "__main__":
    try:
        migrate(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Migration stopped without overwriting files: {exc}") from exc
