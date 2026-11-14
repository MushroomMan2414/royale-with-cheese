"""Install the image's three packages, then start the container's web UI."""

import os
from pathlib import Path

from mornye.extensions import ExtensionManager


def main() -> None:
    Path(os.environ["HOME"]).mkdir(parents=True, exist_ok=True)
    manager = ExtensionManager(auto_install_downloads=False)
    for name in ("utilities.sflx", "spotify-web.sflx", "tidal-web.sflx"):
        extension = manager.install_from_file(Path("/opt/mornye-packages") / name)
        print(f"Installed {extension.name} {extension.version}", flush=True)
    os.execvp(
        "python",
        ["python", "-m", "mornye", "--web", "--host", "0.0.0.0", "--port", "8000"],
    )


if __name__ == "__main__":
    main()
