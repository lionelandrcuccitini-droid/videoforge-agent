# Roadmap

## 0.2 — Editorial intelligence

- PySceneDetect backend and audio-silence boundaries
- Transcript-aware removal of filler words and long pauses
- Pluggable CLIP/VideoMAE/LLM scene scoring
- Beat-aligned cuts and loudness normalization
- Thumbnail/contact-sheet generation for plan review

## 0.3 — Templates and review

- Brand-safe title cards, overlays, watermarks, and transitions
- Web review UI with source preview and EDL editing
- OpenTimelineIO import/export
- Rights metadata and preflight policy checklist

## 0.4 — Production operations

- SQLite/Postgres job ledger and idempotency keys
- Isolated workers, queues, object storage, retries, and observability
- Platform-specific adapters after API/policy review
- Human approval service with immutable audit history
- Content moderation and copyright-risk hooks

Roadmap items are proposals, not commitments. Publisher work must preserve the
explicit approval gate and include a non-network dry-run test.
