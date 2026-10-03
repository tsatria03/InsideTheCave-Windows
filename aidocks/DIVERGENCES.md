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

### Volume settings (port addition, built 2026-10-02)
The original's gains are constants (the music at 0.2, `changeVolumeTo:0.2` at 0x100010a6c). The port keeps every one and adds two settings on top, in `settings.json`: `MASTERVOLUME`, which Page Up and Page Down step by ten, and `MUSICVOLUME`. Both default to 100, the original's mix (`platform/volume.py`; `project_port_plan.md`, question 12). The game does not apply them yet; the SpriteKit stand-in will.

### Actions keep their leftover time (built 2026-10-02)
SpriteKit runs actions frame by frame, 60 frames a second on the iPhone, so an action that ends partway through a frame hands over to the next one at the following frame. The port's frames come at whatever rate Windows gives, so rounding to them would make every chain of actions run long by a different amount on every computer: the slot chain above all, one slot every 0.165 x `speedMonster` (`moveObstacleWithBorn`, 0x100013ae8). The stand-in (`insidethecave/scene/actions.py`) starts the next action, and any action a block starts, at the exact moment the last one ended, so chains keep the binary's durations whatever the frame rate (`tests/case/scene.py`). On the iPhone the difference was at most a sixtieth of a second a link.

### No sound louder than 1.0 (built 2026-10-02)
The game asks for 3.0 for a roar in the player's lane (0x10000f740) and for the bats there (0x10000f85c), against 1.0 and 0.7 elsewhere. The port plays nothing above 1.0 (the dev: "All sound volumes should not exceed 1.0 to avoid peaking."), so the 3.0 is heard as 1.0 (`insidethecave/scene/audio.py`, `MAX_GAIN`). This is most likely what the iPhone did too, since the volume `changeVolumeTo:` sets runs from 0 to 1 in Apple's audio (**inferred**: Apple's code, not the binary), which would make the original's roar as loud in every lane. The roar's lane is told by where it comes from; the bats keep 1.0 against 0.7.

### Sounds placed by the port's own mapping (built 2026-10-02, to tune by ear)
How SpriteKit turned a node's place into a direction is Apple's code. The port maps it itself (`insidethecave/scene/audio.py`): the distance from the listener in lanes across, the height ahead, OpenAL's inverse distance, HRTF off; the roar, the bats and the coin jingle mixed to mono so they can be placed (`project_port_plan.md`, question 2). The constants are first guesses, for the dev to judge with `tests/interact/scene_check.py`.

### The tutorial line's voice (built 2026-10-02, not yet spoken by the game)
The original speaks it through `AVSpeechSynthesizer` in "en-US", "pt-BR", "es-ES", "zh-CN", "ru-RU" or "fr-FR", at 0.55 for English, 0.6 for Portuguese, Spanish and Chinese, 0.5 for Russian and French (`GameScene.tutorial`, 0x10000dea8). The port speaks it in a SAPI 5 voice through Prism, chosen by Windows' display language rather than the device's (`platform/language.py`), at Prism's rate 0.5, its normal, for every language (the dev: "Yes, it should use rate 0.5, no higher."). With no installed voice for the language, the English line is spoken in SAPI's default voice, so no line is read in a voice for another language (`platform/speech.py`, `TutorialVoice`; `project_port_plan.md`, questions 6 and 7). Where the original crashes on a device with no language (`brk` at 0x10000e830), the port says English.

## Where the port necessarily differs

Expected, not yet written up in detail:

- **Input.** Swipes and taps become keys that can be rebound. Built 2026-10-02 (`platform/keymap.py`, the F1 screen in `ui/keybind_screen.py`): move left A or Left Arrow (the swipe left, 0x100016ee8), move right D or Right Arrow (the swipe right, 0x100016e34), throw W or Up Arrow (the swipe up, 0x100016f98), pause P; F1, Escape, Page Up and Page Down fixed. A tap, which went left or right by where it landed (0x10000fff0), has no key of its own: the two move keys are its two halves. Kept in `keys.json`.
- **The save.** `UserDefaults` becomes `save.json` (`rank`, `countTutorial`, under the binary's own key names) and `settings.json` in `%APPDATA%\InsideTheCave` (`platform/defaults.py`, built 2026-10-02). `rankWorld` is not saved: there is no world ranking.
- **Timers.** The original's four `NSTimer`s run on the port's own run loop (`platform/runloop.py`, built 2026-10-02), on the wall clock, as the original's.
- **Speech.** `AVSpeechSynthesizer` becomes NVDA, another screen reader through Prism, or a Windows voice.
- **The screens.** UIKit screens become lists of rows read aloud.
- **The ranking.** CloudKit's world ranking cannot work.

### The sounds are WAV, sorted into used and unused
The original keeps 12 sounds loose in its bundle's top folder, as WAV, MP3 and AIFF (three with the wrong extension), and loads each by its full file name (`"BatSound.wav"`, `"dash.aiff"`, `"Rugido.mp3"`; see `GAME_STRUCTURE.md`). On 2026-10-02 the dev moved them into `game/sounds/`, converted them to MP3, then the same day to 16-bit PCM WAV, and sorted them, as in their earlier port:
- `game/sounds/used/`: the 12 the 2.32 binary names, under their base names (`Rugido.wav`, `dash.wav`, `tilintar.wav` and the rest).
- `game/sounds/unused/`: 14 sounds from the game's older versions, which 2.32 never names (`GAME_STRUCTURE.md` section 15).

So the port finds a sound by its base name, whatever extension the binary gives: the binary's `"dash.aiff"` is `game/sounds/used/dash.wav`. It looks in `used/` first, then `unused/`. WAV needs no decoder: Python's `wave` module reads it and OpenAL plays it. Two that were 8-bit in the original (`MovimentoProibido`, `screamingMan`) are 16-bit now, and every sound has gone through two conversions; whether each plays as loud and as long as the original is to be checked by ear once the port plays them.
