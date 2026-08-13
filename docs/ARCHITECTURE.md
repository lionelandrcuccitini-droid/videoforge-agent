# Architecture

VideoForge separates creative decisions from media execution. Analysis and planning
produce portable JSON artifacts; rendering and publishing consume only validated
models. This boundary keeps the expensive path deterministic and makes it safe for
an LLM, UI, or human editor to alter a plan without issuing arbitrary shell commands.

## Components

| Component | Responsibility | Side effects |
|---|---|---|
| `config` | Strict YAML validation and path resolution | Reads YAML/source existence |
| `media` | FFprobe metadata and FFmpeg scene boundaries | Runs read-only media processes |
| `planner` | Selects/trims scenes to a target duration | None |
| `renderer` | Compiles one filter graph and atomically replaces output | Writes rendered media |
| `captions` | Runs optional faster-whisper and emits SRT | Downloads model/writes SRT |
| `publishers` | Executes one explicit platform adapter | Network only after approval |
| `agent` | Checkpoint-aware lifecycle orchestration | Coordinates all above |

## Artifact contract

Every run writes its intermediate artifacts under `workspace`:

- `media.json`: probed source properties;
- `scenes.json`: all candidate intervals;
- `edit-plan.json`: selected clips and output geometry;
- `captions.srt`: optional transcription;
- `publication.preview.json`: dry-run publication request.

The plan uses absolute source paths after configuration resolution. This favors
reliable local resumption; a future remote worker protocol should rewrite these to
content-addressed URIs.

## Failure and resumption

Output video is first rendered to a hidden sibling and atomically replaced on
success. An existing plan and final video are reused by default. `--no-resume`
forces fresh analysis/rendering. Model and upload operations are intentionally
outside the core render, so a network or OAuth failure cannot destroy the video.

## Security boundaries

- `subprocess.run` receives an argv list and never invokes a shell.
- YAML uses `safe_load`, Pydantic forbids unknown fields, and source paths must exist.
- Publishing requires both a config switch and a command-line approval switch.
- OAuth tokens and common media files are ignored by Git.
- The webhook requires HTTPS and disables redirects.
- CI uses read-only repository permissions.

Do not expose this CLI directly as a multi-tenant web service without adding media
size limits, path sandboxing, job isolation, quotas, SSRF controls, and malware/content
screening.

