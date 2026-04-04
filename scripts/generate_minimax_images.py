#!/usr/bin/env python3

import argparse
import pathlib

from minimax_common import download_file, post_json, read_text, write_json


def main():
    parser = argparse.ArgumentParser(description="Generate one or more MiniMax images and save all candidates")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--model", default="image-01")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--n", type=int, default=4)
    parser.add_argument("--prompt-optimizer", choices=["true", "false"], default="true")
    args = parser.parse_args()

    if not args.prompt and not args.prompt_file:
        raise RuntimeError("Either --prompt or --prompt-file is required.")

    prompt = args.prompt.strip() if args.prompt else read_text(args.prompt_file).strip()

    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "model": args.model,
        "prompt": prompt,
        "aspect_ratio": args.aspect_ratio,
        "response_format": "url",
        "n": args.n,
        "prompt_optimizer": args.prompt_optimizer == "true",
    }

    _, response_json = post_json("/v1/image_generation", payload)
    data = response_json.get("data", {})
    image_urls = data.get("image_urls", [])
    if response_json.get("base_resp", {}).get("status_code") != 0 or not image_urls:
        raise RuntimeError(str(response_json))

    candidates = []
    for index, image_url in enumerate(image_urls, start=1):
        image_path = output_dir / f"candidate-{index:02d}.png"
        download_file(image_url, image_path)
        candidates.append(
            {
                "index": index,
                "image_url": image_url,
                "image_path": str(image_path),
            }
        )

    write_json(output_dir / "response.json", response_json)
    write_json(
        output_dir / "summary.json",
        {
            "model": payload["model"],
            "aspect_ratio": payload["aspect_ratio"],
            "count": len(candidates),
            "prompt_optimizer": payload["prompt_optimizer"],
            "prompt": prompt,
            "candidates": candidates,
            "success_count": response_json.get("metadata", {}).get("success_count"),
            "failed_count": response_json.get("metadata", {}).get("failed_count"),
        },
    )
    print((output_dir / "summary.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
