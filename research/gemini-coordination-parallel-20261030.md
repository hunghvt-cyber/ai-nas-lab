# Gemini wrapper coordination lessons — 2026-10-30

This is reusable coordination guidance; task-specific keys, timings, findings,
and evidence remain with the originating project report.

## Before delegating

- Read `/home/admin/bin/gemini-task --help` and inspect the wrapper implementation. Check whether `--key` pins an identity, whether calls are concurrency-safe, how state locks work, what input formats are accepted, and whether image review is supported.
- Do not conclude the tool is unavailable because a single invocation failed. Diagnose the actual wrapper or quota error; do not rotate identities to evade a limit.
- Give each reviewer a narrow, independent question and the same sanitized source/measurements. Do not expose one reviewer’s answer to another during independent review.
- Never send user content, session material, tokens, secrets, or raw private logs. The wrapper’s ability to accept a prompt does not imply it is appropriate to send every artifact.

## Parallelism and review stages

- Parallelize only independent analyses after checking concurrency safety. In this workflow, up to three bounded analysis calls ran concurrently; two final reviews also ran concurrently. Keep concurrency smaller when tasks share context or reviewers might contaminate one another.
- Separate initial design analysis from final diff/evidence review. A second pass should target only findings affected by code/evidence changes, not repeat the whole review.
- If the wrapper is text-only, have Gemini assess structured descriptions and measurements, but do not attribute visual inspection to it. Use a reviewer/tool that can inspect screenshots for pixel-level claims.
- The primary implementer remains responsible for verifying each finding against source and tests; do not apply suggestions by vote.

## Measure coordination honestly

- Record per-call start/end/duration and phase wall time when evaluating coordination. If only aggregate timing exists, label it approximate; do not infer missing per-call values.
- Track errors, timeouts, retries, concurrency, and the implementer’s active preparation/verification effort separately.
- Do not claim time saved without a comparable no-delegation baseline. Useful findings (for example, a defect or independent risk caught) are evidence of contribution, not a numeric time-saving measurement.
- Keep project-specific proof, review answers and call logs in that project’s handoff; this shared lab should contain reusable process lessons, not private application context.
