# Download albums and tracks from a CSV

This guide covers two ways to use a CSV with the Docker example:

- **Makefile:** one terminal command resolves the CSV and starts downloading.
- **HTTP API:** your program resolves the CSV, then submits each returned URL
  as a separate download job.

Both approaches use the `downloads/` folder in this repository. For initial
Docker requirements and setup, see [Docker setup](docker-setup.md).

## 1. Prepare a CSV

Create a UTF-8 file named `my-music.csv` with a `URL` column, for example:

```csv
URL
https://open.spotify.com/album/REPLACE_WITH_ALBUM_ID
https://open.spotify.com/track/REPLACE_WITH_TRACK_ID
```

Replace the placeholders with real links before using the file. An **album
link expands to its tracks**; a **track link selects that track**. Other
catalogue links may work when the corresponding metadata extension is
installed. A bare list of links without a header also works.

Mornye can also search common track exports containing a title, artist or
ISRC. Text-only rows are searched as *tracks*: an album name in such a row
does not request the whole album. Use an album URL for that.

## 2. Option A: run it with Make

Open a terminal in `royale-with-cheese` and run:

```sh
make csv CSV="/path/to/my-music.csv"
```

Use the real path to your file. For a file in this directory, use
`make csv CSV="my-music.csv"`. The command builds and starts the app if
needed, streams the file into the container, then downloads using
`ext:tidal-web`. The input file's parent directory is not mounted into the
container. Progress and errors appear in the terminal; the command waits for
the CSV run to finish.

Mornye treats the resolved list as one playlist, deduplicates tracks, skips
existing files it recognizes, and writes an M3U8 playlist named after the CSV
in `downloads/`. Check the output for unmatched rows and failures: a completed
command does not guarantee every item was downloaded. To open the folder on
macOS:

```sh
open downloads
```

Other useful commands: `make up` starts the web app, `make ps` shows its
status, `make logs` follows web-app logs (Ctrl+C stops following), and
`make down` stops it without deleting downloads.

## 3. Option B: use the API

Start the app from this directory:

```sh
make up
```

The examples below use `curl` and Python 3, available on a typical macOS
setup. The API is at `http://127.0.0.1:18080`; if you changed `MORNYE_PORT`,
use that port instead. The interactive documentation is at
<http://127.0.0.1:18080/docs>.

### Resolve the CSV

The endpoint takes **file contents in JSON**, not a server-side file path.
This command converts your local UTF-8 CSV into the required JSON, posts it,
and saves the response as `csv-resolution.json`:

```sh
python3 -c 'import json, pathlib; p = pathlib.Path("my-music.csv"); print(json.dumps({"name": p.name, "content": p.read_text(encoding="utf-8-sig")}))' \
  | curl --fail-with-body --silent --show-error \
      -H 'Content-Type: application/json' \
      --data-binary @- http://127.0.0.1:18080/api/v1/csv/resolve \
  > csv-resolution.json
```

Change `my-music.csv` to your file path. The destination response file is
overwritten if it already exists. Inspect it with:

```sh
python3 -m json.tool csv-resolution.json
```

The response contains `urls` (deduplicated resolved links), `resolved`, and
`unresolved` rows. Rows containing a link retain it; text-only rows may
require a catalogue search. **This call does not queue or download anything.**

### Queue a resolved URL

Copy one actual URL from the `urls` array into the request below. An album
URL queues the album; a track URL queues that track. Repeat for each URL you
want to download:

```sh
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://open.spotify.com/track/REPLACE_WITH_TRACK_ID","quality":"LOSSLESS","services":["ext:tidal-web"]}' \
  http://127.0.0.1:18080/api/v1/downloads
```

The response is HTTP **202 Accepted**, with a job `id` and `status`; it means
the job was accepted, not that downloading succeeded. Save the ID to check
its progress:

```sh
curl --fail-with-body --silent --show-error \
  http://127.0.0.1:18080/api/v1/downloads/REPLACE_WITH_JOB_ID
```

You can list jobs with `curl http://127.0.0.1:18080/api/v1/downloads`. Check
job status, errors, and the `downloads/` folder; provider availability,
matching, authentication or verification challenges can prevent downloads.
The API submits separate jobs rather than the single CSV playlist run used by
`make csv`, so it does not create that CSV-named playlist as part of the API
flow.

The example server is unauthenticated and bound to host localhost. The API
inherits any authentication configured on the host; see the upstream
[REST API guide](https://github.com/mornyeapp/Mornye-Python/blob/dcff676/docs/guide/rest-api.md)
before exposing it elsewhere. The upstream
[CSV reference](https://github.com/mornyeapp/Mornye-Python/blob/dcff676/docs/guide/csv.md)
describes additional formats and matching options.
