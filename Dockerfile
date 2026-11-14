FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp/mornye-home \
    DISPLAY=:99 \
    MORNYE_DATA_DIR=/data \
    MORNYE_DOWNLOAD_DIR=/downloads

# Chromium and Xvfb support provider flows that need a browser; tini forwards
# signals and reaps child processes. Node runs JavaScript extensions.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates chromium ffmpeg flac fonts-liberation nodejs procps tini xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files needed to build the host, not the checkout's .env,
# local state, git history, or any unrelated files.
COPY --from=host pyproject.toml README.md LICENSE MANIFEST.in /build/
COPY --from=host mornye/ /build/mornye/
RUN pip install --no-cache-dir /build && rm -rf /build \
    && groupadd --gid 10001 mornye \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /tmp/mornye-home mornye \
    && mkdir -p /data /downloads /opt/mornye-packages \
    && chown 10001:10001 /data /downloads

COPY --from=packages utilities.sflx spotify-web.sflx tidal-web.sflx /opt/mornye-packages/
COPY examples/docker_entrypoint.py /opt/mornye-entrypoint.py
COPY examples/csv_download.py /opt/csv-download.py

USER 10001:10001
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/mornye-entrypoint.py"]
