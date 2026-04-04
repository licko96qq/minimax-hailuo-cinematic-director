#!/usr/bin/env python3

import argparse
import json
import pathlib
import subprocess

from minimax_common import read_json, write_json


def run_command(args):
    completed = subprocess.run(args, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Execute a multi-shot Hailuo story package")
    parser.add_argument("--story-package", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--from-shot", type=int, default=1)
    parser.add_argument("--to-shot", type=int, default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-audit-check", action="store_true")
    parser.add_argument("--skip-review", action="store_true")
    parser.add_argument("--review-output-dir", default=None)
    parser.add_argument("--with-soundtrack", action="store_true")
    parser.add_argument("--soundtrack-output-dir", default=None)
    args = parser.parse_args()

    story_package_path = pathlib.Path(args.story_package).resolve()
    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    package = read_json(story_package_path)
    story_base_dir = story_package_path.parent
    audit_report_path = story_base_dir / "audit-report.json"
    if not args.skip_audit_check:
        if not audit_report_path.exists():
            raise RuntimeError(
                f"Audit report not found: {audit_report_path}. Run audit_story_package.py before generation, "
                "or pass --skip-audit-check to bypass."
            )
        audit_report = read_json(audit_report_path)
        if not audit_report.get("passed"):
            raise RuntimeError(
                f"Audit failed for story package {story_package_path}. "
                "Rewrite the package before generation, or pass --skip-audit-check to bypass."
            )
    manifest = {
        "story_package": str(story_package_path),
        "audit_report": str(audit_report_path) if audit_report_path.exists() else None,
        "shots": [],
    }

    shot_results = {}
    for shot in package["shots"]:
        shot_number = int(shot["shot_id"].split("-")[-1])
        if shot_number < args.from_shot:
            if shot.get("status") == "existing":
                shot_results[shot["shot_id"]] = pathlib.Path(shot["video_path"]).resolve()
            continue
        if args.to_shot and shot_number > args.to_shot:
            break

        shot_output_dir = output_dir / shot["shot_id"]
        shot_output_dir.mkdir(parents=True, exist_ok=True)

        shot_record = {
            "shot_id": shot["shot_id"],
            "title": shot["title"],
            "mode": shot.get("input_mode", shot.get("status", "t2v")),
            "status": "planned" if not args.execute else "running",
            "tags": shot.get("tags", []),
        }

        if shot.get("status") == "existing":
            resolved_video = pathlib.Path(shot["video_path"]).resolve()
            shot_results[shot["shot_id"]] = resolved_video
            shot_record["status"] = "existing"
            shot_record["video_path"] = str(resolved_video)
            manifest["shots"].append(shot_record)
            continue

        first_frame_path = None
        if shot.get("input_mode") == "i2v":
            anchor_from = shot["anchor_from"]
            anchor_video = shot_results.get(anchor_from)
            if anchor_video is None:
                prior_summary = output_dir / anchor_from / "summary.json"
                if prior_summary.exists():
                    anchor_video = pathlib.Path(read_json(prior_summary)["video_path"]).resolve()
                    shot_results[anchor_from] = anchor_video
            if anchor_video is None and not args.execute:
                shot_record["anchor_from"] = anchor_from
                shot_record["anchor_status"] = "deferred-until-previous-shot-exists"
            elif anchor_video is None:
                raise RuntimeError(f"Missing anchor video for {shot['shot_id']}: {anchor_from}")
            if anchor_video is not None:
                first_frame_path = shot_output_dir / "anchor.png"
                extract_cmd = [
                    "python3",
                    str(pathlib.Path(__file__).with_name("extract_frame.py")),
                    "--video",
                    str(anchor_video),
                    "--output",
                    str(first_frame_path),
                    "--mode",
                    shot.get("frame_position", "end"),
                ]
                if shot.get("frame_position") == "seconds" and shot.get("frame_offset_seconds") is not None:
                    extract_cmd.extend(["--seconds", str(shot["frame_offset_seconds"])])
                elif shot.get("frame_offset_seconds") is not None:
                    extract_cmd.extend(["--end-offset", str(shot["frame_offset_seconds"])])
                run_command(extract_cmd)
                shot_record["anchor_frame"] = str(first_frame_path)

        shot_record["prompt_en"] = shot["prompt_en"]
        shot_record["prompt_zh"] = shot["prompt_zh"]
        shot_record["model"] = shot["model"]
        shot_record["duration"] = shot["duration"]
        shot_record["resolution"] = shot["resolution"]
        shot_record["prompt_optimizer"] = shot["prompt_optimizer"]

        if args.execute:
            generate_cmd = [
                "python3",
                str(pathlib.Path(__file__).with_name("generate_hailuo_video.py")),
                "--prompt",
                shot["prompt_en"],
                "--output-dir",
                str(shot_output_dir),
                "--model",
                shot["model"],
                "--duration",
                str(shot["duration"]),
                "--resolution",
                shot["resolution"],
                "--prompt-optimizer",
                "true" if shot["prompt_optimizer"] else "false",
            ]
            if first_frame_path:
                generate_cmd.extend(["--first-frame-image", str(first_frame_path)])
            run_command(generate_cmd)
            summary = read_json(shot_output_dir / "summary.json")
            video_path = pathlib.Path(summary["video_path"]).resolve()
            shot_results[shot["shot_id"]] = video_path
            shot_record["status"] = "generated"
            shot_record["summary_path"] = str((shot_output_dir / "summary.json").resolve())
            shot_record["video_path"] = str(video_path)
        else:
            shot_record["status"] = "planned"

        manifest["shots"].append(shot_record)

    manifest_path = output_dir / "generation-manifest.json"
    write_json(manifest_path, manifest)

    if args.execute and not args.skip_review:
        review_output_dir = pathlib.Path(args.review_output_dir).resolve() if args.review_output_dir else (
            story_base_dir / "review"
        ).resolve()
        review_cmd = [
            "python3",
            str(pathlib.Path(__file__).with_name("review_generated_sequence.py")),
            "--story-package",
            str(story_package_path),
            "--generation-manifest",
            str(manifest_path),
            "--output-dir",
            str(review_output_dir),
        ]
        run_command(review_cmd)
        manifest["review_report"] = str((review_output_dir / "review-report.json").resolve())
        manifest["review_summary"] = str((review_output_dir / "review-summary.md").resolve())
        manifest["sequence_preview"] = str((review_output_dir / "sequence-preview.mp4").resolve())
        write_json(manifest_path, manifest)

        if args.with_soundtrack:
            soundtrack_output_dir = (
                pathlib.Path(args.soundtrack_output_dir).resolve()
                if args.soundtrack_output_dir
                else (story_base_dir / "soundtrack").resolve()
            )
            soundtrack_cmd = [
                "python3",
                str(pathlib.Path(__file__).with_name("run_soundtrack_pipeline.py")),
                "--story-package",
                str(story_package_path),
                "--sequence-preview",
                str(review_output_dir / "sequence-preview.mp4"),
                "--output-dir",
                str(soundtrack_output_dir),
                "--execute",
            ]
            run_command(soundtrack_cmd)
            manifest["soundtrack_manifest"] = str((soundtrack_output_dir / "soundtrack-manifest.json").resolve())
            manifest["final_with_music"] = str((soundtrack_output_dir / "final-with-music.mp4").resolve())
            manifest["soundtrack_review_summary"] = str(
                (soundtrack_output_dir / "soundtrack-review-summary.md").resolve()
            )
            write_json(manifest_path, manifest)

    print(json.dumps({"manifest": str(manifest_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
