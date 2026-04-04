#!/usr/bin/env python3

import argparse
import pathlib

from minimax_common import (
    check_success,
    download_file,
    file_to_data_url,
    post_json,
    retrieve_file,
    wait_for_video,
    write_json,
)


def main():
    parser = argparse.ArgumentParser(description="Generate one Hailuo video and save all artifacts")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default="MiniMax-Hailuo-2.3")
    parser.add_argument("--duration", type=int, default=6)
    parser.add_argument("--resolution", default="768P")
    parser.add_argument("--prompt-optimizer", choices=["true", "false"], default="false")
    parser.add_argument("--first-frame-image", default=None)
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "model": args.model,
        "prompt": args.prompt.strip(),
        "duration": args.duration,
        "resolution": args.resolution,
        "prompt_optimizer": args.prompt_optimizer == "true",
    }

    if args.first_frame_image:
        first_frame_path = pathlib.Path(args.first_frame_image)
        if first_frame_path.exists():
            payload["first_frame_image"] = file_to_data_url(first_frame_path)
        else:
            payload["first_frame_image"] = args.first_frame_image

    _, create_response = post_json("/v1/video_generation", payload)
    check_success(create_response)
    task_id = create_response["task_id"]
    write_json(output_dir / "create.response.json", create_response)

    query_response = wait_for_video(task_id)
    write_json(output_dir / "query.response.json", query_response)

    file_id = query_response["file_id"]
    file_response = retrieve_file(file_id)
    write_json(output_dir / "file.response.json", file_response)

    download_url = file_response["file"]["download_url"]
    video_path = output_dir / "output.mp4"
    download_file(download_url, video_path)

    summary = {
        "model": payload["model"],
        "task_id": task_id,
        "file_id": file_id,
        "video_path": str(video_path),
        "video_width": query_response.get("video_width"),
        "video_height": query_response.get("video_height"),
        "prompt": payload["prompt"],
        "duration": payload["duration"],
        "resolution": payload["resolution"],
        "prompt_optimizer": payload["prompt_optimizer"],
    }
    if "first_frame_image" in payload:
        summary["first_frame_image_mode"] = "provided"
    write_json(output_dir / "summary.json", summary)
    print((output_dir / "summary.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
