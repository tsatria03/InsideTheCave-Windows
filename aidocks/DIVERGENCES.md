# Divergences from the original

The rule for this port is: reproduce what the binary does, including what looks like a
mistake, and write the mistake down here rather than fixing it. Anything listed as
"reproduced" is deliberate. Every deliberate difference is listed here too, with why.

Each entry gives the address it rests on, and the port's matching code. Before
"reproducing" anything that hinges on one branch or constant, check the raw bytes.

---

## Original behaviour kept as-is

Nothing yet (2026-10-02).

## Where the port differs on purpose

Nothing yet.

## Where the port necessarily differs

Expected, not yet written up in detail:

- **Input.** Swipes and taps become keys that can be rebound.
- **Speech.** `AVSpeechSynthesizer` becomes NVDA, another screen reader through Prism, or a Windows voice.
- **The screens.** UIKit screens become lists of rows read aloud.
- **The ranking.** CloudKit's world ranking cannot work.

### The sounds are MP3, in a folder of their own
The original keeps 12 sounds loose in its bundle's top folder, as WAV, MP3 and AIFF, and loads each by its full file name (`"BatSound.wav"`, `"dash.aiff"`, `"Rugido.mp3"`; see `GAME_STRUCTURE.md`). The dev moved them into `game/sounds/` and converted every one to MP3 on 2026-10-02, keeping the base names (the two that were MP3 already were re-encoded too). So the port has to find a sound by its base name: the binary's `"SC.wav"` is `game/sounds/SC.mp3`. Whether a converted sound plays as loud and as long as the original is to be checked by ear once the port plays them.
