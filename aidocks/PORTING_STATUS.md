# Porting status

What is done, what is stubbed, what has not been started. Kept honest: "done" means
ported from the disassembly method by method, with the address recorded in the code.

---

## Done

Nothing yet (2026-10-02).

## Stubbed: present, body empty, call sites intact

Nothing yet.

## Not ported

Everything. The original's nine classes, from `GAME_STRUCTURE.md`:

- `AppDelegate`
- `WarningViewController`
- `HomeScreenViewController`
- `GameViewController`
- `GameScene`
- `ResultViewController`
- `RankingViewController` and `TableCell`
- `RankingCloud` (CloudKit; cannot work as it was)

## The platform layer

Not started: OpenAL, the run loop (for `SKAction` waits and sequences, `Timer` and the scene's `update:`), the save (for `UserDefaults`), speech (for `AVSpeechSynthesizer`), the key map and the key-bindings screen.

## The analysis

Not started: no arm64 tools, no disassembly listings yet (see `project_binary_analysis_notes.md`).
