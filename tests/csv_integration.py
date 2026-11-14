"""Offline integration check against the Mornye installed in the container."""

import asyncio
from pathlib import Path
import tempfile

from mornye.core.models import TrackMetadata
from mornye.downloader import DownloadOptions, MornyeDownloader


async def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        csv = root / "input.csv"
        album_url = "https://open.spotify.com/album/album123"
        track_url = "https://open.spotify.com/track/track123"
        csv.write_text(f"URL\n{album_url}\n{track_url}\n", encoding="utf-8")
        downloader = MornyeDownloader(
            DownloadOptions(output_dir=str(root / "music"), services=["ext:none"])
        )

        def track(id, title):
            return TrackMetadata(
                id=id, title=title, artists="Test Artist", album="Test Album",
                album_artist="Test Artist",
            )

        catalogue = {
            album_url: [track("one", "Album track one"), track("two", "Album track two")],
            track_url: [track("three", "Single track")],
        }

        async def resolve(url):
            return "Test", catalogue[url], {}

        async def resolve_isrc(tracks):
            return list(tracks)

        selected = []

        async def download(plan, options):
            selected.extend(item.track.title for item in plan.pending)
            return {}

        downloader._resolve_metadata_async = resolve
        downloader._resolve_isrc_bulk_async = resolve_isrc
        downloader._download_pending_async = download
        result = await downloader.run_csv_async(str(csv))
        assert result["resolved"] == 2
        assert result["tracks"] == 3
        assert selected == ["Album track one", "Album track two", "Single track"]
        print("Mixed album and track CSV expanded to three tracks")


if __name__ == "__main__":
    asyncio.run(main())
