---
name: project_provenance
description: "Inside The Cave was made by Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife (MacMagazine, 2016-09-06, read by the dev). The Windows port is a solo project by tsatria03, with no contributors now or planned. How to credit."
metadata:
  node_type: memory
  type: project
---

**The original's makers:** Iago Barbosa, Juliana Barros and Victor Leal, a trio at **BEPiD Recife**, Apple's iOS developer training program in Brazil (later the Apple Developer Academy).
- **Source:** MacMagazine, "Inside The Cave é o jogo mais acessível que você vai conhecer", by Priscila Klopper, 2016-09-06: https://macmagazine.com.br/post/2016/09/06/inside-the-cave-e-o-jogo-mais-acessivel-que-voce-vai-conhecer/ . The page says the game was "developed by the trio Iago Barbosa, Juliana Barros, and Victor Leal from BEPiD Recife".
- **How it was found (2026-10-02):** nothing in `Info.plist` or the binary names a maker. A web search found the article, but the site refused Claude's fetch (HTTP 403), so the dev opened it in their browser and pasted the page, which confirmed the names word for word.
- The game is **no longer on the App Store**; the article's store box says "this app is no longer available in the store".
- No second source names Juliana Barros or Victor Leal. Iago Barbosa has an ArtStation page and a Medium article about an illustrated "Inside The Cave" project (a creature explores a cave and a monster chases it out), which fits but does not itself say he made the game.

**The original:** display name "Inside The Cave", bundle identifier `InsideTheCaveBD`, version 2.32, built with Xcode 8.2 against the iOS 10.2 SDK, in Swift 3 with SpriteKit, for iPhone, iPad and Apple TV. Its internal names and log messages are Portuguese (`monstroPedra`, `Erro ao salvar`). Whether the `BD` in the bundle identifier stands for BEPiD is a guess, not a fact.

**The port is solo.** tsatria03 is the only person working on it, and will not add contributors (the dev, 2026-10-02: "I'm the only one who is going to work on the game. I'm not going to add any contributors.").

**Why:** Credit matters, and the code itself doesn't say who made the original.

**How to apply:**
- README and `docks/credits.txt`: the suggested wording is "Inside The Cave was made by Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife." Then "tsatria03 made the Windows port." No contributors list. Confirm the final wording with the dev when those files are written.
- The changelog carries no credit lines ([[feedback_changelog]]).
- Commits: tsatria03 is the author; no `Co-authored-by:` lines for people ([[feedback_use_github_usernames]], [[feedback_git_commits]]).
- `LICENSE` is MIT; change its copyright line only if the dev asks.
- The game's sounds, images and data under `game/` are the original makers', not covered by the port's license.
