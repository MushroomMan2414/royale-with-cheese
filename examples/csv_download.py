"""Run Mornye's CSV downloader on a file streamed through standard input."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1] or Path(sys.argv[1]).name != sys.argv[1]:
        raise SystemExit("Expected one CSV filename")

    # Compose starts the container asynchronously; wait for its entrypoint to
    # finish installing extensions and for the web process to become ready.
    deadline = time.monotonic() + 90
    while True:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=2):
                break
        except (OSError, urllib.error.URLError):
            if time.monotonic() >= deadline:
                raise SystemExit("Mornye did not become ready; check make logs")
            time.sleep(1)

    with tempfile.TemporaryDirectory(prefix="mornye-csv-") as temporary:
        csv_path = Path(temporary) / sys.argv[1]
        with csv_path.open("wb") as destination:
            shutil.copyfileobj(sys.stdin.buffer, destination)
        command = [
            sys.executable,
            "-m",
            "mornye",
            "--csv",
            os.fspath(csv_path),
            "/downloads",
            "--service",
            "ext:tidal-web",
        ]
        return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
