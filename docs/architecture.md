# Architecture and extension lifecycle

## The mental model

Mornye-Python is the **host**: it provides the interfaces, configuration,
metadata and download orchestration, storage, and extension runtimes.
Mornye-Extension is a **distribution repository**: it contains provider
source, packaged extensions, and catalogs describing where packages can be
downloaded. Installing the host does not install this catalog or its
providers by default.

```text
Mornye-Extension                         Mornye-Python
----------------                         -------------
sources/<provider>/                      CLI / TUI / web / Python API
  manifest.json + index.js                        |
       |                                          v
       v                               metadata + download orchestration
extensions/*.sflx  <--- registry JSON             |
       |                 id, version, URL,         v
       |                 checksum       installed extension directory
       +-------------------------------→ JS bridge / Python loader
                                                  |
                                                  v
                                      provider service → output files
```

An extension can contribute **metadata**, **downloads**, or another
capability. These roles are separate: `spotify-web`, for example, declares
itself a metadata provider, whereas `tidal-web` declares both metadata and
download capabilities. A Spotify link does not imply that Spotify supplies the
audio; a selected download provider must find a matching recording.

## Repository map

| Area | Purpose |
| --- | --- |
| `Mornye-Extension/sources/<provider>/` | Reviewable JavaScript provider source and manifest. |
| `Mornye-Extension/extensions/` | Distributable `.sflx` ZIP archives. `utilities.sflx` is a Python package for this host. |
| `Mornye-Extension/registry.json` | JavaScript extension catalog. |
| `Mornye-Extension/registry-python.json` | Python utilities catalog. |
| `Mornye-Extension/registry-unified.json` | Generated combined catalog, with runtime markers. |
| `Mornye-Python/mornye/client.py` | Public `Mornye` and `AsyncMornye` entry points. |
| `Mornye-Python/mornye/application/` | Download, metadata, provider selection, and coordination services. |
| `Mornye-Python/mornye/core/` | Models, metadata, matching, tags, downloads, storage, and other shared services. |
| `Mornye-Python/mornye/extensions/` | Registry management, package installation, JS bridge, and Python loader. |
| `Mornye-Python/mornye/frontend/`, `tui/`, `webapi/` | Web/desktop frontend, terminal UI, and versioned API. |

## Packages, manifests, and registries

The source-backed JavaScript packages contain `manifest.json`, `index.js`,
license notices, and sometimes an icon. The manifest names the extension and
declares its version, capabilities, URL patterns, settings, and permissions.
For example, Tidal declares `download_provider` and `metadata_provider`,
quality options, network domains, and signed-session runtime requirements.

Registry entries describe distributions: an ID, version, package download
URL, and optionally a SHA-256 digest and signature. The registry ID is used
for lookup; the manifest's `name` determines the installed extension name.
The `utilities` entry points to `utilities.sflx`, which supplies modules such
as Spotify metadata, signed-session support, and the browser solver. It is a
runtime utility rather than a download provider.

For source-backed JavaScript packages, the store's
`scripts/build_packages.py` builds reproducible archives and refreshes the
registry version and checksum; `--check` compares expected outputs without
writing. The unified catalog is generated from the JS and Python registries.
The Python utilities archive is maintained separately, not built by that
script. Some archives may be package-only, so source and build procedures
should be checked for the particular provider.

## Discovery, installation, and updates

1. The host collects registry URLs from `MORNYE_REGISTRIES`, supported `.env`
   files, and persisted GUI/CLI/API registry settings. There is no default
   registry. `MORNYE_REGISTRIES` accepts comma-separated URLs.
2. With automatic extension synchronization enabled, `ExtensionManager`
   fetches the configured catalogs. In this version it attempts to install or
   update **every entry**, including metadata and utility extensions—not only
   the download service selected for a request. Utilities are processed first.
3. For each registry entry, the manager applies its minimum trust tier,
   downloads the archive, verifies its SHA-256 when provided, checks ZIP
   contents and paths, and stages the installation under the extension
   directory. Existing settings are preserved on replacement.
4. The manager compares installed version and stored registry checksum against
   the entry. It rechecks on subsequent work after
   `MORNYE_EXT_UPDATE_INTERVAL` seconds (default `3600`); `0` limits the
   check to once per process. A failed fetch or individual install can be
   logged without stopping all other entries.

Automatic bootstrap is invoked in several entry paths, including entering an
`AsyncMornye` context and constructing download providers. Passing
`sync_extensions=False` to `AsyncMornye` suppresses the context-entry sync;
it does not globally disable every later manager bootstrap. The local example
instead uses isolated state and no configured registry.

`ExtensionManager(auto_install_downloads=False).install_from_file(path)` is a
separate local installation path. It reads a ZIP directly rather than looking
up a registry entry: there is no registry signature or checksum to verify.
The example uses this deliberately, so it installs exactly the three named
local packages. Updates require rerunning the installation after updating the
local archives.

### Trust and execution boundaries

The available registry trust tiers are `unverified`, `checksum-only`, and
`signed`; `MORNYE_MIN_TRUST` sets the minimum. A digest checks that the bytes
match the registry entry, but does not independently establish who authored
the entry. A verified Ed25519 signature requires a trusted public key.
Local-file installs bypass the registry trust-tier check. Extensions are
executable code: choose and review the packages and sources you run.

The JavaScript bridge launches a Node process with a restricted environment
and network/filesystem guard helpers. These are defense-in-depth measures,
not a claim of complete isolation. Python extensions are imported directly
into the host process and must be trusted accordingly.

## Runtime and provider selection

For a JavaScript provider, `JSExtensionProvider` reads the installed manifest
and settings, creates `JSRuntime` instances, and delegates calls to the Node
bridge. Python and Node exchange newline-delimited JSON messages over
stdin/stdout; responses, errors, and progress are routed back to the caller.
The bridge exposes host-like HTTP, file, storage, and session operations.
Some signed-session operations are forwarded to Python support modules.

For a Python download provider, `PythonExtensionProvider` imports the
installed entry point in-process and requires exactly one `BaseProvider`
subclass. It adapts the provider to the host's download interface. Python
runtime utilities such as `utilities` are loaded through their own gateway.

`services` / `--service` specifies provider preference, for example
`ext:tidal-web`. Legacy aliases such as `tidal` map to installed extension
IDs. For a service with both implementations, the factory normally tries the
JavaScript provider first and a matching Python provider as a fallback;
explicit `-web` and `-py` names constrain that choice. Provider availability,
quality support, matching, and remote service behavior still determine
whether a particular track succeeds.

## A download, end to end

The exact path varies by input and interface; the following is a conceptual
trace for a Spotify track with Tidal selected:

1. The CLI, web UI, or Python API accepts a source URL and options. The
   asynchronous API opens shared HTTP resources and can synchronize configured
   extensions when its context is entered.
2. Spotify metadata support resolves the source to `TrackMetadata`, including
   fields such as title, artist, duration, and potentially ISRC. Other
   catalogue URLs can be handled by a matching installed extension. Metadata
   and download sources can differ.
3. The application resolves eligible providers and constructs an adapter for
   the selected extension. It asks the provider to locate and fetch the
   recording, falling through to eligible alternatives when appropriate.
4. The host and provider perform the applicable validation and post-processing:
   for example FLAC checks, tags, lyrics, optional transcoding, and history.
   The recording guard can reject a positively identified wrong recording;
   it does not prove that every accepted match is correct.
5. Files go to the requested output directory. Success, skips, and failures
   are reported by the relevant interface. `AsyncMornye.download_track()`
   returns a list of failed tracks (an empty list indicates none were
   reported), rather than a single output path.

The newer `DownloadService` and structured `DownloadRequest` / `DownloadReport`
coexist with legacy download adapters; not every convenience method traverses
exactly the same application-layer path. See `client.py` and
`application/download_service.py` for the specific entry point being used.

## State and configuration

`MORNYE_DATA_DIR` overrides `~/.mornye` for durable host state, including the
database, extensions, registry settings, and session data. `MORNYE_EXT_DIR`
can override the extension directory independently. The default cache is
under the data directory and can be overridden with `MORNYE_CACHE_DIR`.
Download output is a separate path; for web mode `MORNYE_DOWNLOAD_DIR` sets
the default. If using containers, persist both data and download locations.

## Further reading

- [Local setup and example](local-setup.md)
- [Mornye-Python extension guide](https://github.com/mornyeapp/Mornye-Python/blob/dcff676/docs/guide/extensions.md)
- [Mornye-Python Python extension development](https://github.com/mornyeapp/Mornye-Python/blob/dcff676/docs/guide/python-extensions.md)
- [Extension store and build instructions](https://github.com/mornyeapp/Mornye-Extension/blob/12530ce/README.md)
