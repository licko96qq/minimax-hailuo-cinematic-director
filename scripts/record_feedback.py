#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import pathlib

from minimax_common import read_json, write_json


def main():
    parser = argparse.ArgumentParser(description="Record user feedback for a Hailuo story run")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--shot-id", required=True)
    parser.add_argument("--score", type=int, required=True)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = pathlib.Path(args.run_dir).resolve()
    manifest_path = run_dir / "generation-manifest.json"
    manifest = read_json(manifest_path)

    matching = [shot for shot in manifest["shots"] if shot["shot_id"] == args.shot_id]
    if not matching:
        raise RuntimeError(f"Shot not found in manifest: {args.shot_id}")
    shot = matching[0]

    feedback_entry = {
        "recorded_at": dt.datetime.now().isoformat(timespec="seconds"),
        "run_dir": str(run_dir),
        "shot_id": args.shot_id,
        "score": args.score,
        "notes": args.notes,
        "title": shot.get("title"),
        "tags": shot.get("tags", []),
    }

    feedback_path = run_dir / "feedback.json"
    existing_feedback = []
    if feedback_path.exists():
        existing_feedback = json.loads(feedback_path.read_text(encoding="utf-8"))
    existing_feedback.append(feedback_entry)
    write_json(feedback_path, existing_feedback)

    global_log_path = pathlib.Path(__file__).resolve().parents[1] / "output" / "feedback-log.ndjson"
    global_log_path.parent.mkdir(parents=True, exist_ok=True)
    with global_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")

    print(json.dumps(feedback_entry, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
