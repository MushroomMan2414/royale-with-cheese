#!/bin/sh
# Copy the previous Compose download volume once, before switching to the bind mount.
set -eu

project=$(docker compose config --format json | python3 -c 'import json, sys; print(json.load(sys.stdin)["name"])')
volume="${project}_mornye-downloads"
marker=".mornye-migration/${project}.done"
mkdir -p downloads .mornye-migration

if [ -f "$marker" ]; then
    exit 0
fi

if docker volume inspect "$volume" >/dev/null 2>&1; then
    # Prevent writes to the old volume while it is being copied. The volume is
    # deliberately retained so migration can be retried or inspected.
    docker compose stop mornye
    stage=$(mktemp -d "${TMPDIR:-/tmp}/mornye-migrate.XXXXXXXX")
    container=""
    cleanup() {
        if [ -n "$container" ]; then docker rm -f "$container" >/dev/null; fi
        rm -rf "$stage"
    }
    trap cleanup EXIT HUP INT TERM
    container=$(docker create --network none --read-only \
        --mount "type=volume,source=${volume},target=/old,readonly" \
        --entrypoint /bin/true royale-mornye-local)
    docker cp "$container:/old/." "$stage/"
    python3 scripts/migrate_downloads.py "$stage" downloads
    cleanup
    trap - EXIT HUP INT TERM
    printf '%s\n' "Existing downloads copied from $volume. The original volume was retained."
fi

touch "$marker"
