# Design references

Research was performed in August 2026. These projects/models informed architecture
and tradeoffs; VideoForge is an independent implementation and does not vendor or
copy their source code.

## GitHub projects

- [LosslessCut](https://github.com/mifi/lossless-cut) demonstrates an FFmpeg-first
  workflow, inspectable segment projects, broad container support, and the value of
  lossless operations where possible. VideoForge similarly treats FFmpeg as the
  execution engine, while focusing on unattended batch workflows and accepting
  re-encoding for normalized social formats.
- [editly](https://github.com/mifi/editly) demonstrates a declarative edit spec.
  VideoForge's validated `edit-plan.json` follows the same broad idea: decisions are
  data, separate from rendering.
- [MoviePy](https://github.com/Zulko/moviepy) provides approachable Python
  composition primitives. Its documentation notes the flexibility/performance
  tradeoff; VideoForge therefore avoids frame-level Python processing in its hot path.
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) shows a mature scene
  manager and interoperable timecode/EDL exports. The MVP uses FFmpeg's built-in
  scene score to minimize dependencies; PySceneDetect is a natural future backend.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) provides efficient
  CTranslate2 Whisper inference, word timestamps, batched transcription, and VAD.
  It is the optional local subtitle backend.
- [Remotion](https://github.com/remotion-dev/remotion) demonstrates programmatic
  video and reusable visual templates. VideoForge retains an FFmpeg core to stay
  small, but a Remotion renderer would suit branded motion-graphics templates.
- [Vex](https://github.com/AKMessi/vex) demonstrates a conversational editing agent
  and safe working-copy principle. It is source-available/non-commercial, so it was
  used only as product research, not as a code dependency.

## Hugging Face models

- [openai/whisper-large-v3-turbo](https://huggingface.co/openai/whisper-large-v3-turbo)
  is a pruned large-v3 speech-recognition model with four decoding layers. The model
  card describes a substantial speed gain with a small quality tradeoff and MIT
  licensing; it motivates the default subtitle model name `large-v3-turbo`.
- [facebook/timesformer-base-finetuned-k400](https://huggingface.co/facebook/timesformer-base-finetuned-k400)
  and the Transformers
  [TimeSformer documentation](https://huggingface.co/docs/transformers/model_doc/timesformer)
  demonstrate spatiotemporal video classification. VideoForge does not enable this
  by default because action labels are not equivalent to editorial quality and the
  added model cost is large. The scene `score` field is the integration point for a
  future visual semantic ranker.

## Adopted and rejected choices

| Decision | Choice | Reason |
|---|---|---|
| Media engine | FFmpeg CLI | Mature codec/filter support and one-process rendering |
| Timeline contract | Strict JSON model | Reviewable, portable, replayable |
| Scene backend | FFmpeg scene filter | Zero additional base dependency |
| ASR | Optional faster-whisper | Local inference; base install remains lightweight |
| Visual understanding | Deferred adapter | Generic action labels do not reliably rank narrative value |
| Publisher | Plugin protocol + approval gate | Platform credentials and policies stay isolated |
| Default publication | Dry-run/private | Prevent accidental public uploads |

Always review upstream licenses and model cards before adding a dependency or model,
especially for commercial use.

