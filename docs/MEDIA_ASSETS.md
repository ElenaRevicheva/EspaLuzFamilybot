# Base media assets are not committed

The video features in this repository composite audio over a short looping base
clip with ffmpeg. Those base clips are **not** in git.

## Why

They are tens of megabytes of unscannable binary. A licence reviewer cannot certify
bytes it cannot read, so carrying them here blocks the repository from passing a
supply-chain scan — and they are not source in any meaningful sense.

## What you need to supply

Drop these in the repository root:

| file | what it is |
| --- | --- |
| `looped_video.mp4` | ~30 s silent loop, the base for generated video posts |
| `espaluz_loop.mp4` | short loop used as a lightweight fallback |
| `espaluz_conversation_mode.mp4` | base clip for conversation-mode replies (EspaLuzWhatsApp only) |
| `espaluz_conversation_mode_english.mp4` | English variant of the above (EspaLuzWhatsApp only) |

Any silent MP4 of roughly the right length works; nothing depends on their content.

## What happens without them

Nothing breaks. Every path checks first — `create_video_with_looped_base()` and its
siblings call `os.path.exists(base_video)`, log `Base video <name> not found`, and
return `False`. Text, audio and image replies are unaffected.
