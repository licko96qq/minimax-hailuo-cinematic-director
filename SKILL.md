---
name: minimax-hailuo-cinematic-director
description: Plan and generate cinematic multi-shot videos with MiniMax Hailuo 2.3. Use when Codex needs to turn a topic, reference clip, or desired mood into a director-grade three-shot story with treatment, storyboard, shot list, continuity spine, English production prompts, audit scoring, and Hailuo video runs; especially for 2-3 connected six-second clips, follow-up shots that continue an existing video, or showcase sequences where each shot must stay story-continuous while being visually and narratively distinct.
---

# MiniMax Hailuo Cinematic Director

Use this skill as a film-director workflow, not as a raw API wrapper. The job is to spend scarce Hailuo quota on a tightly reviewed three-shot story package.

## Non-negotiable rule

Every three-shot sequence must be:

- story-continuous
- world-continuous
- visually different shot-to-shot
- narratively progressive shot-to-shot

Do not generate if Shot 2 and Shot 3 are only minor variations of the same view.

## Required planning outputs

Before generating, always produce:

- `director-brief.md`
- `storyboard.md`
- `shotlist.md`
- `prompts.md`
- `music-plan.md`
- `story-package.json`
- `distinctness-check.md`
- `audit-report.json`
- `audit-summary.md`（中文）
- generated-sequence review outputs after rendering:
  - `review/review-report.json`
  - `review/review-summary.md`（中文）
  - `review/sequence-preview.mp4`
- soundtrack planning and delivery outputs when music is requested:
  - `soundtrack-audit-report.json`
  - `soundtrack-audit-summary.md`（中文）
  - `soundtrack/soundtrack-manifest.json`
  - `soundtrack/final-with-music.mp4`
  - `soundtrack/soundtrack-review-summary.md`（中文）

## Default workflow

1. Clarify the brief in Chinese.
   Lock topic, desired emotion, realism level, human presence, camera energy, and quota budget.
2. Write a three-shot story package.
   Treat the three shots as:
   - setup
   - escalation
   - payoff
3. Build a `continuity spine`.
   Define what must stay continuous across all shots:
   - world and geography
   - light and time of day
   - emotional objective
4. Build a `difference matrix`.
   For each adjacent pair of shots, force at least three major differences across:
   - camera height
   - framing scale
   - primary subject
   - dramatic beat
   - motion pattern
   - human presence
   - input mode
5. Audit the package before generation.
   Run `scripts/audit_story_package.py`. If the score is weak or the distinctness check fails, rewrite the package first.
6. Only then ask for confirmation and spend video quota.
7. Review the rendered sequence before delivery.
   Run `scripts/review_generated_sequence.py` or rely on `scripts/run_story_sequence.py --execute`, which now runs the review step by default.
8. When soundtrack is requested, plan soundtrack before generating it.
   Create `music_plan`, run `scripts/audit_soundtrack_plan.py`, and only then spend MiniMax music quota.
9. Keep the silent preview and the music-backed final as two separate files.
   Never overwrite `review/sequence-preview.mp4`.

## Production defaults

- Default model when no special constraint is given: `MiniMax-Hailuo-2.3`
- Duration: `6`
- Resolution: `768P`
- Prompt language: English
- User-facing discussion: Chinese
- `prompt_optimizer`: `false` when exact cinematic control matters
- Prefer `i2v` for Shot 2 when continuing a real Shot 1
- Allow Shot 3 to switch back to `t2v` if chained anchors would cause repetitive output

## Two execution modes

Do not collapse these into one mental model.

### Mode 1: `MiniMax-Hailuo-2.3`

This is the primary mode and must remain available.

- Treat it as the standard cinematic three-shot workflow.
- It supports the usual mixed planning structure:
  - Shot 1: `t2v` world setup
  - Shot 2: `i2v` continuation when useful
  - Shot 3: `t2v` or `i2v` depending on distinctness needs
- Use this mode when the user wants maximum freedom for establishing shots and payoff shots.
- Do not replace this mode just because `Fast` exists.

### Mode 2: `MiniMax-Hailuo-2.3-Fast`

This is the secondary mode, not a full replacement for Mode 1.

- Treat it as `image-to-video first`.
- Do not assume plain `t2v` support.
- If the sequence starts from scratch, first generate several `image-01` still candidates and choose the correct anchor frame before spending `Fast` video quota.
- For `Fast`, continuity should be carried through:
  - selected setup anchor still
  - optional chained `i2v` continuation for Shot 2
  - separate payoff anchor still for Shot 3 when needed
- Prefer staged execution instead of spending all three shots in one command.
- When the user asks for `Fast`, explicitly preserve the existence of Mode 1 in planning and documentation.
- Before running `Fast`, verify anchor still quality. If the file extension says `.png` but the bytes are actually JPEG, do not assume the extension is truthful.
- The current scripts now encode `first_frame_image` by sniffing the real file header, not only the filename extension.

## Storyboard contract

For each shot, write all of these fields:

- title
- dramatic purpose
- story beat
- primary subject
- new information introduced
- camera height
- framing
- camera movement
- continuity anchors
- difference axes
- must not repeat
- Chinese intent
- English production prompt

Read [references/cinematic-storytelling.md](references/cinematic-storytelling.md) for the narrative structure and scoring rubric.
Read [references/continuity-rules.md](references/continuity-rules.md) for continuity anchors.
Read [references/hailuo-shot-playbook.md](references/hailuo-shot-playbook.md) for prompt construction.
Read [references/soundtrack-playbook.md](references/soundtrack-playbook.md) for MiniMax soundtrack planning and delivery rules.

## Soundtrack contract

Every three-shot package should also define a `music_plan` with:

- model
- mode
- vocal policy
- goal
- duration strategy
- target video duration
- overall arc
- palette
- Chinese soundtrack prompt
- English soundtrack prompt
- lyrics
- cue sheet aligned to all shots
- mix plan

MiniMax music currently requires a `lyrics` field. For instrumental background music, use structural placeholder lyrics instead of real singable text.

## Audit and scoring

The skill must include an explicit review step before generation.

Audit three layers:

1. Story
   Check setup, escalation, and payoff are all present and not collapsed into the same beat.
2. Shot language
   Check consecutive shots differ in camera height, framing, subject emphasis, and narrative function.
3. Prompt quality
   Check prompts are concrete, production-ready, and not near-duplicates.

Use `scripts/audit_story_package.py` to generate:

- pass/fail
- total score
- sub-scores for story, continuity, distinctness, and prompt quality
- concrete rewrite notes when weak
- Chinese markdown summary by default

Do not proceed to generation if the audit fails.

After generation, use `scripts/review_generated_sequence.py` to generate:

- per-shot contact sheets
- adjacent-shot SSIM checks
- a stitched preview mp4
- a post-generation pass/fail report
- a Chinese markdown review summary by default

Do not deliver the sequence if the review flags adjacent shots as too similar.

When music is requested, also use:

- `scripts/audit_soundtrack_plan.py`
- `scripts/generate_minimax_music.py`
- `scripts/mix_sequence_soundtrack.py`
- `scripts/review_soundtrack_fit.py`
- `scripts/run_soundtrack_pipeline.py`

Do not overwrite the silent preview. Deliver the music-backed version as a separate final.

## Scripts

- `scripts/plan_story_package.py`
  Create the director package, storyboard, prompts, and distinctness report.
- `scripts/audit_story_package.py`
  Score the planned package and block weak or repetitive three-shot plans.
- `scripts/extract_frame.py`
  Extract a frame from a local video for continuity anchoring.
- `scripts/generate_hailuo_video.py`
  Send a single Hailuo text-to-video or image-to-video request and save all artifacts.
- `scripts/generate_minimax_images.py`
  Generate multiple image anchors first when `Fast` should start from selected stills.
- `scripts/run_story_sequence.py`
  Execute a multi-shot package in order, automatically extracting anchor frames between shots and running post-generation review by default. Use `--with-soundtrack` when you also want the soundtrack pipeline.
- `scripts/review_generated_sequence.py`
  Review the rendered sequence with contact sheets, adjacent-shot SSIM checks, a stitched preview, and a pass/fail report.
- `scripts/audit_soundtrack_plan.py`
  Score whether the soundtrack plan is narratively and technically suitable before spending music quota.
- `scripts/generate_minimax_music.py`
  Generate one MiniMax music cue and save raw response plus summary.
- `scripts/mix_sequence_soundtrack.py`
  Mix the generated soundtrack into the silent preview without overwriting the original file.
- `scripts/review_soundtrack_fit.py`
  Review whether the soundtrack + video combination is suitable for delivery.
- `scripts/run_soundtrack_pipeline.py`
  Run soundtrack audit, music generation, mixing, and soundtrack review end to end.
- `scripts/run_soundtrack_candidates.py`
  Generate, audit, mix, review, rank, and promote multiple soundtrack candidates against the same silent preview.
- `scripts/record_feedback.py`
  Save user ratings and notes so future runs can reuse what worked.

## Built-in sample

Use `assets/iceland-continuation-brief.json` when continuing the Iceland glacier river clip into a three-shot story. This sample must produce:

- Shot 1: high aerial establishing river world
- Shot 2: a tighter, lower, more narrative clue shot
- Shot 3: a clearly different payoff shot with a new composition and emotional function

Typical flow:

```bash
python3 scripts/plan_story_package.py \
  --preset iceland-continuation \
  --existing-shot-video /abs/path/to/video.mp4 \
  --output-dir output/runs/iceland-continuation

python3 scripts/audit_story_package.py \
  --story-package output/runs/iceland-continuation/story-package.json \
  --report output/runs/iceland-continuation/audit-report.json \
  --markdown output/runs/iceland-continuation/distinctness-check.md

python3 scripts/run_story_sequence.py \
  --story-package output/runs/iceland-continuation/story-package.json \
  --output-dir output/runs/iceland-continuation/generated \
  --from-shot 2 \
  --execute

python3 scripts/run_soundtrack_pipeline.py \
  --story-package output/runs/iceland-continuation/story-package.json \
  --sequence-preview output/runs/iceland-continuation/review/sequence-preview.mp4 \
  --output-dir output/runs/iceland-continuation/soundtrack \
  --execute
```

## Learning loop

Do not auto-rewrite the skill instructions after each run.

Instead:

1. Save the run package and outputs.
2. Save audit scores and user feedback.
3. Reuse high-scoring story structures, camera plans, and prompt patterns in future runs.

The goal is stable process improvement, not uncontrolled drift.
