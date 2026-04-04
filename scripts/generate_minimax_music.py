#!/usr/bin/env python3

import argparse
import pathlib

from minimax_common import check_success, download_file, post_json, write_json


def main():
    parser = argparse.ArgumentParser(description="Generate one MiniMax music cue and save all artifacts")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default="music-2.5")
    parser.add_argument("--lyrics", default="")
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "model": args.model,
        "prompt": args.prompt.strip(),
        "stream": False,
        "output_format": "url",
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
        },
    }
    if args.lyrics.strip():
        payload["lyrics"] = args.lyrics.strip()

    _, response_json = post_json("/v1/music_generation", payload)
    check_success(response_json)

    audio_data = response_json["data"]["audio"]
    audio_path = output_dir / "output.mp3"
    if isinstance(audio_data, str) and audio_data.startswith("http"):
        download_file(audio_data, audio_path)
    else:
        audio_path.write_bytes(bytes.fromhex(audio_data))

    response_path = output_dir / "response.json"
    summary_path = output_dir / "summary.json"
    write_json(response_path, response_json)
    write_json(
        summary_path,
        {
            "model": payload["model"],
            "prompt": payload["prompt"],
            "lyrics_included": "lyrics" in payload,
            "audio_path": str(audio_path),
            "duration_ms": response_json.get("extra_info", {}).get("music_duration"),
            "sample_rate": response_json.get("extra_info", {}).get("music_sample_rate"),
            "bitrate": response_json.get("extra_info", {}).get("bitrate"),
            "size_bytes": response_json.get("extra_info", {}).get("music_size"),
        },
    )
    print(summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
