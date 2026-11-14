"""Install the three example archives from the sibling extension checkout."""

from pathlib import Path

from mornye.extensions import ExtensionManager


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "Mornye-Extension" / "extensions"
    manager = ExtensionManager(auto_install_downloads=False)
    for filename in ("utilities.sflx", "spotify-web.sflx", "tidal-web.sflx"):
        path = root / filename
        if not path.is_file():
            raise SystemExit(f"Missing extension package: {path}")
        extension = manager.install_from_file(path)
        print(f"{extension.name}: {extension.manifest.get('version')} ({extension.runtime})")


if __name__ == "__main__":
    main()
