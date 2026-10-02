# Inside The Cave: how the game works

The mechanism of the game as read out of `game/InsideTheCave`, with addresses.
Addresses are VM addresses; file offset = address - 0x100000000
(see `project_binary_analysis_notes.md`).

**Status, 2026-10-02: nothing here is verified from the code yet.** Everything below is
read from the binary's strings, selector names, property names and the bundle's files,
or from the press article in section 0. Names suggest; only the code proves. Each claim
moves from "inferred" to "verified, at 0x..." as the disassembly is read.

---

## 0. What the makers' press said

From MacMagazine, 2016-09-06 (see `project_provenance.md`), describing the game as it
was then. These are a reviewer's words, not the code's.

- You are in a very dark cave, and your torch is gradually going out.
- Monsters are in the cave. When you hear the roar, tap the screen to move right or left and avoid it.
- The torch can be thrown at monsters as a weapon, and you find more torches along the way.
- "With the latest update ... new monsters and even a boss have been added."
- A leaderboard compares scores with other players.
- VoiceOver narrates, for example, the position of the torches. The narrations are in Portuguese, English, Spanish, French, Russian and Chinese.
- It ran on iPhone, iPod touch, iPad and Apple TV, and was free.
- A reader's comment under the article says the app crashed after a lost game and did not record the score. It may point to a bug in the game-over path; check it when that code is read.

**Which version we have.** Our binary was built with Xcode 8.2 (`DTXcodeBuild` 8C1002) and the iOS 10.2 SDK, released in December 2016, after the article. So version 2.32 most likely includes the update the article describes, with the new monsters and the boss. The `...2` monster names in section 3 may be the new monsters. No string names a boss, and only three of the six narration languages have been found so far; both are open (`project_dev_tasks.md`).

## 1. The bundle

- Display name "Inside The Cave", bundle `InsideTheCaveBD`, version 2.32.
- Swift 3, SpriteKit, Xcode 8.2, iOS 10.2 SDK, arm64 only, portrait only.
- Fonts: `Apple ][.ttf`, `Fipps-Regular.otf`, `PressStart2P.ttf`, `3Dventure.ttf`.
- SpriteKit scenes: `GameScene.sks`, `Actions.sks`, `Snow.sks` (a particle effect).
- Images are in the compiled asset catalogue `Assets.car`.

## 2. The classes

Nine game classes (inferred from strings; the count matches `__objc_classlist`):

- `AppDelegate`
- `WarningViewController`: the first screen, "Put the earphone on for a better experience", on a timer, then the `WarningToMenu` segue.
- `HomeScreenViewController`: the menu.
- `GameViewController`: hosts the scene, shows the score and coin labels, and takes the `GameToResult` segue when the scene calls its `GameOverDelegate`.
- `GameScene`: the game itself, an `SKScene` and `SKPhysicsContactDelegate`.
- `ResultViewController`: the score, a name field ("Insert name", "unnamed player"), replay and back to the menu.
- `RankingViewController` and `TableCell`: the ranking table, with a segmented control (`selectTable`) between two tables.
- `RankingCloud`: the online ranking, through CloudKit's public database (`publicDB`, record type `Ranking`/`rankWorld`).

## 3. The game (inferred)

**The lanes.** Three: `positionLaneZero`, `positionLaneOne`, `positionLaneTwo`. The player is in `actualPositionPlayer`. Swipes (`UISwipeGestureRecognizer`) and taps (`UITapGestureRecognizer`, `movePlayerTap`) move left or right (`movePlayerLeft`, `movePlayerRight`). A move past the edge plays `MovimentoProibido.wav` ("forbidden move"). `blockPlayer` stops movement.

**The tutorial line**, spoken through `AVSpeechSynthesizer` in the device's language and shown a limited number of times (`countTutorial`):
- English: "You need to scape from a cave full of monsters on the way! When you hear the roar, swipe or tap to the other side!"
- Spanish and Portuguese versions say the same.

**Obstacles.** Monsters come down the lanes, moved by `moveObstacle`, chosen by `choiceObstacleLine`, `choiceObstacleCoin` and `lineRandom`. Kinds: rock (`monstroPedra`, `monstroPedra2`), ice (`monstroGelo`, `monstroGelo2`), crystal (`monstroCristal`, `monstroCristal2`), bats (`morcego1` to `3`) and `torchObstacle`. Their speed is `speedMonster`. A roar plays at the monster's position (`playMonsterRoarAtPoint:`, `Rugido.mp3`, `createRoarSensor`); bats have their own (`playBatSoundAtPoint:`, `BatSound.wav`).

**Dying.** `obstacleDidCollideWithPlayer:obstacleE:` sets `playerDead`; `screamingMan.wav` plays, then the game-over delegate.

**Torches and light.** The scene is lit by an `SKLightNode` whose falloff shrinks (`falloffSize`, `changeFalloffSize`). Picking up a torch (`playerDidCollideWithTorch:`, `pegou_tocha.wav`) and throwing it (`throwTorch`, `throwLightTorch`, `lancar_tocha.wav`) are in the game, with `tocha.wav` as a burning loop (`createBackgroundTorch`).

**Killing.** `torchDidCollideWithBat:batB:` and `torchDidCollideWithObstacle:obstacleE:` exist, with `MonsterDead.mp3` and death sprites for each monster kind (`deadPedra.png`, `deadGelo.png`, `deadCristal.png`). So a thrown torch likely kills bats and monsters; which kinds, and what it scores, is unverified.

**Coins.** Rock, ice and water coins (`rockCoin`, `iceCoin`, `waterCoin`), picked up by `playerDidCollideWithCoin:playerP:`, with `plim_moeda.wav` and `tilintar.aiff`. Counters per scenario (`CoinCounter`, `coinCounterIce`, `coinCounterWater`).

**Score.** `startScore`, `scoreUpWithValue:`, `coinUpWithValue:`, `upScore`. Saved best scores in `UserDefaults` (`Score`, `Pontuacao`, `player2`, `player3`).

**Scenarios.** The cave changes as you go: `cenarioPedra`, `cenarioPedraAgua`, `cenarioAgua`, `cenarioAguaGelo`, `cenarioGelo` (`scenario0` to `2`, `changeScenario`, `moveScenario`).

**Sound files.** The original keeps them in the bundle's top folder; the dev moved them into `game/sounds/` on 2026-10-02, names unchanged. All 12 are named in the binary and nowhere else (not in the `.sks` scenes or the storyboards), so the code plays every one.

**What each sound is for (2026-10-02).** Ten are loaded one after another, in the same order, by three functions, `0x100015620`, `0x100015d58` and `0x100017154`, most likely the three initialisers of `GameScene`. That order matches, one for one, ten consecutive stored properties in Swift's field list (`__swift3_reflstr`, 0x100028310). **Verified:** which string is loaded where, and the two orders matching. **Inferred:** that each file belongs to the field in the same place, and what each field means, from its name (Portuguese file names translated).

- `Rugido.mp3`: `roar`, the monster's roar ("rugido", roar). Loaded at 0x1000157d8.
- `BatSound.wav`: `batSound`, the bats. 0x100015830.
- `tilintar.aiff`: `coinTinkle` ("tilintar", to jingle); likely a coin ahead jingling so it can be found by ear; `moveCoinSound` suggests it moves with the coin. 0x100015884.
- `plim_moeda.wav`: `coinSound` ("plim moeda", coin ding); likely picking a coin up. 0x1000158d8.
- `pegou_tocha.wav`: `getTorchSound` ("pegou tocha", got torch). 0x10001592c.
- `lancar_tocha.wav`: `playTorchSound` ("lançar tocha", throw torch). 0x100015980.
- `tocha.wav`: `backgroundTorch` ("tocha", torch); likely the held torch burning in a loop. 0x1000159d4.
- `SC.wav`: `backgroundMusic`, the game music (16.6 MB; confirmed by the dev). 0x100015a28.
- `dash.aiff`: `movePlayerSound`, the dash to another lane. 0x100015a7c.
- `MonsterDead.mp3`: `deadMonster`, a monster or bat dying. 0x100015ad0.

The other two are loaded elsewhere:
- `MovimentoProibido.wav` ("forbidden move"), in two functions, `0x10000f8e4` (load at 0x10000f988) and `0x10000fb90` (0x10000fc14). Two functions fits a move left and a move right that each refuse at the cave's edge; unverified.
- `screamingMan.wav`, in one function, `0x1000230c4` (load at 0x100023148), away from the scene's sounds; likely the player's scream at death. Unverified.

The addresses come from a hand decode of arm64 `adr` and `adrp`+`add` pairs, with functions bounded by `LC_FUNCTION_STARTS`. None of these functions is an Objective-C method, so none has a name yet.

## 4. What needed a server

- The world ranking, through CloudKit. It cannot work in a port; how to replace it (a local table, or nothing) is the dev's decision.
