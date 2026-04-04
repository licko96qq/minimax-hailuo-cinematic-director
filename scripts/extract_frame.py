#!/usr/bin/env python3

import argparse
import json
import pathlib
import subprocess

from minimax_common import ensure_parent


def probe_duration(video_path):
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video_path),
        ],
        text=True,
    )
    return float(json.loads(output)["format"]["duration"])


def main():
    parser = argparse.ArgumentParser(description="Extract a representative frame from a video")
    parser.add_argument("--video", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["start", "middle", "end", "seconds"], default="end")
    parser.add_argument("--seconds", type=float, default=None)
    parser.add_argument("--end-offset", type=float, default=0.12)
    args = parser.parse_args()

    video_path = pathlib.Path(args.video).resolve()
    output_path = pathlib.Path(args.output).resolve()
    ensure_parent(output_path)

    duration = probe_duration(video_path)
    if args.mode == "start":
        timestamp = 0.0
    elif args.mode == "middle":
        timestamp = duration / 2.0
    elif args.mode == "seconds":
        if args.seconds is None:
            raise RuntimeError("--seconds is required when --mode seconds")
        timestamp = args.seconds
    else:
        timestamp = max(duration - args.end_offset, 0.0)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(
        json.dumps(
            {
                "video_path": str(video_path),
                "output_path": str(output_path),
                "timestamp_seconds": round(timestamp, 3),
                "duration_seconds": round(duration, 3),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
