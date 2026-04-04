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
    parser = argparse.ArgumentParser(description="Run soundtrack audit, generation, mix, and fit review")
    parser.add_argument("--story-package", required=True)
    parser.add_argument("--sequence-preview", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--force-music", action="store_true")
    args = parser.parse_args()

    story_package_path = pathlib.Path(args.story_package).resolve()
    sequence_preview_path = pathlib.Path(args.sequence_preview).resolve()
    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    story_base_dir = story_package_path.parent

    audit_report_path = story_base_dir / "soundtrack-audit-report.json"
    audit_summary_path = story_base_dir / "soundtrack-audit-summary.md"

    run_command(
        [
            "python3",
            str(pathlib.Path(__file__).with_name("audit_soundtrack_plan.py")),
            "--story-package",
            str(story_package_path),
            "--report",
            str(audit_report_path),
            "--markdown",
            str(audit_summary_path),
        ]
    )
    audit_report = read_json(audit_report_path)

    manifest = {
        "story_package": str(story_package_path),
        "sequence_preview": str(sequence_preview_path),
        "soundtrack_audit_report": str(audit_report_path),
        "soundtrack_audit_summary": str(audit_summary_path),
    }

    if not args.execute:
        manifest_path = output_dir / "soundtrack-manifest.json"
        write_json(manifest_path, manifest)
        print(json.dumps({"manifest": str(manifest_path)}, ensure_ascii=False, indent=2))
        return

    if not audit_report.get("passed"):
        raise RuntimeError(f"配乐审核未通过：{audit_report_path}")

    package = read_json(story_package_path)
    music_plan = package["music_plan"]
    music_output_dir = output_dir / "music"
    mix_summary_path = output_dir / "mix.summary.json"
    final_output_path = output_dir / "final-with-music.mp4"
    music_summary_path = music_output_dir / "summary.json"
    if args.force_music or not music_summary_path.exists() or not (music_output_dir / "output.mp3").exists():
        generate_cmd = [
            "python3",
            str(pathlib.Path(__file__).with_name("generate_minimax_music.py")),
            "--prompt",
            music_plan["prompt_zh"],
            "--output-dir",
            str(music_output_dir),
            "--model",
            music_plan["model"],
        ]
        if music_plan.get("lyrics"):
            generate_cmd.extend(["--lyrics", music_plan["lyrics"]])
        run_command(generate_cmd)

    mix_plan = music_plan["mix_plan"]
    run_command(
        [
            "python3",
            str(pathlib.Path(__file__).with_name("mix_sequence_soundtrack.py")),
            "--video",
            str(sequence_preview_path),
            "--music",
            str(music_output_dir / "output.mp3"),
            "--output",
            str(final_output_path),
            "--music-volume",
            str(mix_plan["music_volume"]),
            "--fade-in",
            str(mix_plan["fade_in_seconds"]),
            "--fade-out",
            str(mix_plan["fade_out_seconds"]),
            "--summary",
            str(mix_summary_path),
        ]
    )

    run_command(
        [
            "python3",
            str(pathlib.Path(__file__).with_name("review_soundtrack_fit.py")),
            "--story-package",
            str(story_package_path),
            "--mixed-video",
            str(final_output_path),
            "--music-summary",
            str(music_summary_path),
            "--mix-summary",
            str(mix_summary_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    manifest.update(
        {
            "music_summary": str(music_summary_path),
            "mix_summary": str(mix_summary_path),
            "final_with_music": str(final_output_path),
            "soundtrack_review_report": str((output_dir / "soundtrack-review-report.json").resolve()),
            "soundtrack_review_summary": str((output_dir / "soundtrack-review-summary.md").resolve()),
        }
    )
    manifest_path = output_dir / "soundtrack-manifest.json"
    write_json(manifest_path, manifest)
    print(json.dumps({"manifest": str(manifest_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
