---
name: project_player_readme
description: "docks/readme.txt (how to play) and docks/credits.txt (who made it, the licenses), written 2026-10-02 in the reference port's style: plain section titles, one sentence per line, ASCII, LF, no markdown, no developer details. Keep the readme in step with the game in the same commit."
metadata:
  type: project
---

**Written 2026-10-02, at the dev's request**: "Look at how [the reference port] wrote it's player facing readme, and as for credits, read the credits from there, and make a section for it in the ITC credits.txt". **Confirmed by the dev the same day** ("The player docks look good."), the credits' wording included.

- **`docks/readme.txt`**: for players, modelled on the reference port's `docks/readme.txt` in the gitignored `user/` folder ([[feedback_no_other_games]]). Sections: the game, headphones, starting, the main menu, the first three games, controls, how to play, your torch, score and coins, the pause menu, game over, your best five, changing the keys, your save, and a last line pointing to `credits.txt`. Every claim checked against the code when written.
- **`docks/credits.txt`**: the reference readme's last two sections, Credits and Licenses, as a file of their own, since this repository has one. The makers' line is the one [[project_provenance]] suggested, then "tsatria03 made the Windows version from the original game." The licenses match what `compiler.py` puts inside the executable (OpenAL Soft and the NVDA client from `vendor/`, Prism and pygame from the installed packages) and `license.txt` beside it.
- **The format**, as the reference's: a section title alone on a line (no `#`, no colon), its sentences one per line, a blank line between sections; ASCII, LF, no BOM, no contractions ([[user_screen_reader]]: markdown symbols are read aloud). Both ship in the build's `docks` folder (`compiler.SIDE_FILES`).
- Left out, as in the reference: Python, flags, debug mode, tests, building, where the port came from.

**How to apply:** whenever a change alters something the readme says (a key, a menu's rows, the save, how the game plays), update `docks/readme.txt` in the same commit, as with the changelog ([[feedback_changelog]]). The todo list's readme item goes to finished once the dev confirms it ([[feedback_todo_list_format]]).
