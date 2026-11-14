"""Download a single Spotify track with an installed Tidal extension."""

import asyncio
import sys

from mornye import AsyncMornye


async def main(url: str) -> int:
    async with AsyncMornye(
        output_dir="./downloads",
        services=["ext:tidal-web"],
        quality="LOSSLESS",
        embed_lyrics=False,
        enrich_metadata=False,
        sync_extensions=False,
    ) as client:
        failed = await client.download_track(url)
    if failed:
        print(f"{len(failed)} track(s) reported as failed.")
        return 1
    print("No failed tracks reported. Check ./downloads for output.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python examples/download_track.py SPOTIFY_TRACK_URL")
    raise SystemExit(asyncio.run(main(sys.argv[1])))
