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

### The sounds are WAV, sorted into used and unused
The original keeps 12 sounds loose in its bundle's top folder, as WAV, MP3 and AIFF (three with the wrong extension), and loads each by its full file name (`"BatSound.wav"`, `"dash.aiff"`, `"Rugido.mp3"`; see `GAME_STRUCTURE.md`). On 2026-10-02 the dev moved them into `game/sounds/`, converted them to MP3, then the same day to 16-bit PCM WAV, and sorted them, as in their earlier port:
- `game/sounds/used/`: the 12 the 2.32 binary names, under their base names (`Rugido.wav`, `dash.wav`, `tilintar.wav` and the rest).
- `game/sounds/unused/`: 14 sounds from the game's older versions, which 2.32 never names (`GAME_STRUCTURE.md` section 15).

So the port finds a sound by its base name, whatever extension the binary gives: the binary's `"dash.aiff"` is `game/sounds/used/dash.wav`. It looks in `used/` first, then `unused/`. WAV needs no decoder: Python's `wave` module reads it and OpenAL plays it. Two that were 8-bit in the original (`MovimentoProibido`, `screamingMan`) are 16-bit now, and every sound has gone through two conversions; whether each plays as loud and as long as the original is to be checked by ear once the port plays them.
