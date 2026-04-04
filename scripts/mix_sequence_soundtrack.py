#!/usr/bin/env python3

import argparse
import json
import pathlib
import subprocess

from minimax_common import write_json


def probe_duration(path):
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(completed.stdout)["format"]["duration"])


def main():
    parser = argparse.ArgumentParser(description="Mix a generated soundtrack into a silent preview cut")
    parser.add_argument("--video", required=True)
    parser.add_argument("--music", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--music-volume", type=float, default=0.28)
    parser.add_argument("--fade-in", type=float, default=0.8)
    parser.add_argument("--fade-out", type=float, default=1.5)
    parser.add_argument("--summary", default=None)
    args = parser.parse_args()

    video_path = pathlib.Path(args.video).resolve()
    music_path = pathlib.Path(args.music).resolve()
    output_path = pathlib.Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = pathlib.Path(args.summary).resolve() if args.summary else output_path.with_suffix(".summary.json")

    video_duration = probe_duration(video_path)
    music_duration = probe_duration(music_path)
    fade_out_start = max(video_duration - args.fade_out, 0)

    filter_complex = (
        f"[1:a]atrim=0:{video_duration:.3f},asetpts=PTS-STARTPTS,"
        f"volume={args.music_volume},"
        f"afade=t=in:st=0:d={args.fade_in},"
        f"afade=t=out:st={fade_out_start:.3f}:d={args.fade_out}[aout]"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-stream_loop",
            "-1",
            "-i",
            str(music_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output_path),
        ],
        check=True,
    )

    write_json(
        summary_path,
        {
            "video_path": str(video_path),
            "music_path": str(music_path),
            "output_path": str(output_path),
            "video_duration_seconds": round(video_duration, 3),
            "music_source_duration_seconds": round(music_duration, 3),
            "music_volume": args.music_volume,
            "fade_in_seconds": args.fade_in,
            "fade_out_seconds": args.fade_out,
            "looped_music": music_duration < video_duration,
            "trimmed_music": music_duration > video_duration,
        },
    )
    print(summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
