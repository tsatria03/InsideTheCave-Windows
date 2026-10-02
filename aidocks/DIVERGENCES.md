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
