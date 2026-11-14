# Local setup: Python host + three local packages

This example uses the three sibling checkouts shown below. It installs the
Python host in a virtual environment and explicitly installs the local
`utilities`, `spotify-web`, and `tidal-web` packages into an isolated data
directory. It does not configure a registry.

```text
morneyapp-personal/
├── Mornye-Python/
├── Mornye-Extension/
└── royale-with-cheese/       ← run commands here
```

## 1. Prerequisites

- Python 3.11 or later, `pip`, and a working virtual environment.
- Node.js on `PATH` for JavaScript extensions. The extension-store offline
  tests require Node.js 22 or newer.
- `ffmpeg` / `ffprobe` for operations that require conversion or inspection.
- Network access to install Python dependencies and, when actually resolving
  a track or downloading audio, to the relevant provider services. Provider
  availability, credentials, geographic restrictions, and signed-session
  challenges vary.

The package comes from the local Python checkout; it is not pinned to a PyPI
release. Editable installation still downloads dependencies unless they are
already available. You can inspect the archives under
`../Mornye-Extension/extensions/` before installing them.

## 2. Install the host and isolate its state

From `royale-with-cheese`:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ../Mornye-Python
export MORNYE_DATA_DIR="$PWD/.mornye-data"
unset MORNYE_EXT_DIR MORNYE_REGISTRIES
```

These commands use a POSIX shell. Keep `MORNYE_DATA_DIR` set in every shell
where you use the example. It isolates the example from the normal
`~/.mornye` state. The working directory should not contain a `.env` with
`MORNYE_REGISTRIES`; Mornye also checks `~/.mornye_env`. Existing registry
settings under the chosen data directory can also cause automatic installs.
Use a fresh data directory if you need a strictly local-only setup. Don't
delete existing state unless you know you no longer need it.

## 3. Install and inspect the packages

```sh
python examples/install_extensions.py
```

The script calls `install_from_file` on the three local `.sflx` archives and
prints their installed names, versions, and runtimes. It performs no registry
fetch and doesn't contact music services. Local installs do not perform
registry checksum or signature verification; the manager may log a warning
about a missing checksum for each archive. If you update the store checkout,
rerun the script to install the updated local archives.

Expected names are `utilities`, `spotify-web`, and `tidal-web`; the first is
Python and the other two are JavaScript. Spotify provides catalogue metadata;
Tidal is the selected download provider. The utilities package supplies
Python metadata and signed-session modules needed by various host paths.

## 4. Run a track example

Pass a real Spotify **track** URL for material you are entitled to use:

```sh
python examples/download_track.py 'https://open.spotify.com/track/REPLACE_WITH_TRACK_ID'
```

Replace the placeholder with a valid URL. The example requests `LOSSLESS`
from `ext:tidal-web`, writes to `./downloads`, and prints whether any tracks
were reported as failed. An empty failure list alone does not establish that
a file was created, so check the output directory and logs. It disables
optional lyrics and metadata enrichment
to keep the example focused. It makes real network requests; provider-side
availability and matching are not guaranteed. Some signed-session flows can
require a browser or other verification.

The example's `sync_extensions=False` avoids a registry sync at context entry,
but provider construction can still bootstrap configured registries. The
isolation and registry checks in step 2 therefore matter.

Alternatively, after the same installation, start the local web UI:

```sh
mornye --web --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The UI's output directory is separately
configurable; it is not automatically `./downloads`. Stop the server with
Ctrl+C. For remote/container usage, see the upstream Docker and web guides.

## 5. Using a registry instead

For registry-managed installs rather than the local archives, an example
catalog URL is:

```sh
export MORNYE_REGISTRIES='https://raw.githubusercontent.com/mornyeapp/Mornye-Extension/main/registry-unified.json'
```

The unified catalog combines the JavaScript entries with Python utilities.
The URL tracks `main`, so its packages and digests can change. In the host
version described here, automatic bootstrap attempts **all** entries in the
configured catalog and periodically checks for updates. Using a registry is
therefore a different setup from the three-package local example. Check the
catalog, packages, and trust policy before configuring it; a checksum from the
same catalog is not an independent signature.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `No module named mornye` | Activate `.venv` and install the sibling checkout with `python -m pip install -e ../Mornye-Python`. |
| Utilities missing | Confirm `MORNYE_DATA_DIR` is the same in both shells and rerun the installer. Check `MORNYE_EXT_DIR` is not overriding it. |
| Tidal extension missing | Re-run the installer and inspect its output; `ext:tidal-web` is the manifest name. |
| Node or bridge error | Confirm `node --version` works and inspect the host logs. If Node is missing, the host may attempt a package-manager install on first use. |
| No match, challenge, or remote error | Check the URL, provider settings, service availability, credentials and logs; retrying cannot guarantee that the provider has the requested recording. |
| Unexpected extensions appear | Check environment, `.env`, `~/.mornye_env`, and persisted registry settings: automatic bootstrap installs all catalog entries. |

See [the architecture guide](architecture.md) for the full lifecycle and
upstream source links.
