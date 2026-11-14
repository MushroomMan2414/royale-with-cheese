# Docker example: local host and selected extensions

This example builds the sibling `Mornye-Python` checkout and copies exactly
three local packages from `Mornye-Extension`: `utilities.sflx`,
`spotify-web.sflx`, and `tidal-web.sflx`. It starts the Mornye web interface.
The host and packages are taken from the local working trees at build time;
the build also downloads base images and system/Python dependencies.

## Prerequisites

- Make and Python 3.9+, plus Docker Desktop or Docker Engine with Compose and
  BuildKit support for `additional_contexts`.
- The sibling directory layout shown in [local setup](local-setup.md).
- Network access to build the image and, during use, to the relevant services.

Run the following from the `royale-with-cheese` directory:

```sh
make up
```

Open <http://127.0.0.1:18080>. Use `make logs` to follow the logs (Ctrl+C
stops following them without stopping the container) and `make ps` to check
its status. If port 18080 is occupied, choose a different host port before
starting, for example:

```sh
MORNYE_PORT=18081 make up
```

The web server listens on port 8000 *inside* the container, while Compose
publishes it only on the host's loopback interface. The UI is unauthenticated;
do not change the port binding to expose it to other machines without adding
authentication and transport protection. Containers on the same Docker network
can also reach port 8000, so don't attach untrusted containers to that network.
Select Tidal in the UI and provide a valid link to try a download. Provider
availability and browser verification
may affect whether a download succeeds.

For a mixed list of album and track links, use
`make csv CSV="/path/to/list.csv"`; see the [CSV guide](csv.md).

## Persistence and lifecycle

Compose mounts `./downloads` from this repository into `/downloads` inside the
container. Downloads appear there immediately; on macOS, open the folder with:

```sh
open downloads
```

On the first `make up` for a Compose project, an existing download volume from
the earlier example is copied into `./downloads` before starting. The service
is stopped during the copy, and the original volume is retained. The copy is
staged in the host's temporary directory, so allow enough free space there as
well as in `./downloads`. Existing identical files are skipped; if a file
differs, migration stops rather than overwriting it. Unsupported items such as
symlinks also stop migration. Resolve the problem and run `make up` again.

A marker in `.mornye-migration/` records the check even when no old volume
exists. Later starts use the mapped folder without recopying. The migration
only runs through `make up`, not a direct `docker compose up`.

Settings, sessions, the database, and installed extensions remain in a named
Docker volume mounted at `/data`. Stop the service with `make down`; both the
host download folder and the data volume survive. **`docker compose down -v`
deletes the data volume.**

At each start the entrypoint reinstalls the image's three archives into the
data volume, preserving extension settings according to the host installer.
To pick up changed checkouts, run `make up` again. This is a local archive
install: it has no registry checksum or signature verification. Review the
archives and their provenance.
There is no registry configured by this example, but a registry added later
through the UI or persisted state can cause automatic catalog-wide installs
and updates. Use a fresh data volume if you want to start without prior state.

## Isolation and limits

- The image runs as UID/GID `10001`, drops Linux capabilities, enables
  `no-new-privileges`, and uses a read-only root filesystem with a writable
  `/tmp`. The data volume and host `downloads/` folder remain writable. No
  Docker socket or host home directory is mounted.
- Extensions still execute code. They can read and modify data and downloads
  in the writable mounts, access container environment variables, and
  make outbound connections. Docker's default network does **not** prevent
  access to your LAN or other reachable services; apply network policy outside
  this example if that is required.
- The container shares the host kernel and is not a guarantee against a
  container escape. Keep Docker and the host updated and do not add
  `privileged`, host networking, or broad bind mounts.
- Browser-based verification depends on the provider and Docker environment;
  the stricter container settings may require additional investigation if a
  particular verification flow fails.

## Troubleshooting

- **Build fails:** check Docker is running, both sibling checkouts exist, and
  your Compose version supports BuildKit additional contexts.
- **Web page does not load:** check `docker compose ps` and
  `docker compose logs mornye`; check the chosen host port is free.
- **Data volume is not writable:** the image initializes fresh named volumes
  for UID 10001. A pre-existing volume with different ownership needs an
  intentional ownership fix or a new volume; don't run the service as root.
- **Downloads folder is not writable:** on Linux, ensure `downloads/` is
  writable by UID/GID 10001, including permissions on its existing files.
  Docker Desktop may translate bind-mount ownership differently.
- **Extension or provider failure:** inspect the logs and the package source;
  availability, credentials and signed-session challenges are provider-specific.
