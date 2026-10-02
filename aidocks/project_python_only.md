---
name: project_python_only
description: "The Windows port of Inside The Cave is written entirely in Python: pygame for the window and keyboard, OpenAL Soft through ctypes for 3D audio, NVDA or Prism for speech. The package is insidethecave/ with game, platform and ui subpackages."
metadata:
  node_type: memory
  type: project
---

The port is written entirely in Python, per `requirements.txt` (`pygame`, `prismatoid`):
- **pygame** for the window, the keyboard and the frame loop. It must be `pygame`, not `pygame-ce`; the two cannot be installed side by side. Initialise only `pygame.display` (and `pygame.font`), never `pygame.init()`, which would open SDL's mixer as a second audio device.
- **OpenAL Soft through ctypes** for all sound, from `vendor/openal/soft_oal.dll` (and `libopenal.so.1` for Linux). The original's positional `SKAudioNode`s (`setPositional:`, `setListener:`) map onto OpenAL sources and the listener.
- **The NVDA controller client** (`vendor/nvda/nvdaControllerClient64.dll`), then **Prism** (`prismatoid`) for other screen readers and a Windows voice. This stands in for the original's `AVSpeechSynthesizer`, which spoke the tutorial line.

Don't propose moving parts to another language or engine.

**Layout to follow** (the empty folders already exist): an entry script at the root, and the `insidethecave/` package with `paths.py`, `game/` (one module per original class), `platform/` (OpenAL, the run loop, the save, speech, the key map) and `ui/` (keyboard input and the key-bindings screen). The platform layer is game-agnostic and can be adapted from the reference port in the gitignored `user/` folder ([[feedback_no_other_games]]).

**Why:** The dev's choice for their ports; the requirements file and folders were set up before the first session.

**How to apply:** Write any new code in Python and follow this layout. Never run the game or build without the dev's say-so ([[feedback_dont_run_or_build]]).
