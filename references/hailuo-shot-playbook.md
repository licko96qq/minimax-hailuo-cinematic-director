# Hailuo Shot Playbook

## Prompt formula

Use one compact production sentence built from:

`subject + environment + action/change + camera + atmosphere`

For Hailuo 6-second clips, this usually performs better than vague poetic writing.

## What to specify

- Subject: what the viewer should care about
- Environment: where it happens and what visual world must remain stable
- Action/change: the one thing that evolves in the shot
- Camera: one intentional move only
- Atmosphere: lighting, realism, emotional finish

## Reliable camera patterns

- aerial push-in
- controlled descent
- lift reveal
- slow orbit
- locked frame with environmental motion

Use Chinese motion tags like `[推进]` or `[拉升]` only when they make the camera move more explicit. Do not stack multiple tags unless you are deliberately testing control limits.

## 6-second constraints

- Do not ask for three unrelated actions in one shot.
- Do not change location unless the clip is intentionally surreal.
- Keep subject identity and light direction stable.
- One emotional beat per shot is enough.

## Text-to-video vs image-to-video

- Use text-to-video when worldbuilding the first shot.
- Use image-to-video when continuing the same scene and composition from a previous shot.
- In image-to-video prompts, describe what changes after the anchor frame, not the entire world from scratch.
- If chained anchors make Shot 3 look like another version of Shot 2, deliberately switch the payoff shot back to `t2v` and preserve continuity through story logic instead of visual lock-in.

## When quality matters more than quota

- Turn `prompt_optimizer` off.
- Write the English prompt manually.
- Use precise natural-language camera instructions.
- Keep the shot architecture simple enough that Hailuo can complete it cleanly.
