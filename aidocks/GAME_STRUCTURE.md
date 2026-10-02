# Inside The Cave: how the game works

The mechanism of the game as read out of `game/InsideTheCave` (version 2.32), with addresses. Addresses are VM
addresses; file offset = address - 0x100000000 (`project_binary_analysis_notes.md`). The listings are in
`analysis/disasm/`, one file per class; `python tools/dz.py <address>` lists one function.

**Status, 2026-10-02: read from the code.** The whole of `__text` was disassembled (`tools/coverage.py`: complete)
and read by three readers working from the listings, one for the scene's setup, input and light, one for what
comes at the player, one for the other screens and the ranking. Their key claims were then checked against the
instructions by hand (each marked **checked** below). Everything here is read from the instructions unless it
says **inferred**, which means it rests on names, strings, or how SpriteKit or UIKit behave.

Names in quotes are the file names the binary asks for. The repository's sounds are MP3 under the same base
names since 2026-10-02 (`DIVERGENCES.md`).

---

## 0. What the makers' press said, and how it compares

From MacMagazine, 2016-09-06 (`project_provenance.md`): a dark cave, a torch going out, monsters you dodge by
their roar, tapping left or right; the torch can be thrown at monsters; "with the latest update ... new monsters
and even a boss"; a leaderboard; VoiceOver; narration in six languages.

Against the code:
- **The six languages are there**: the tutorial line in English, Portuguese, Spanish, Chinese, Russian and
  French (section 8).
- **There is no boss.** No string, node, health or code path for one exists in 2.32. The "new monsters" are
  the crystal and ice skins of the same monster, by scenario (section 5).
- **A thrown torch kills monsters but never bats**; a bat it hits dodges into another lane (section 7).
- The binary was built with Xcode 8.2 (December 2016), after the article, so a boss removed later, or never
  shipped, cannot be told apart from here.

---

## 1. The classes and the screens

Nine classes (`analysis/data/classes.txt`):
- `AppDelegate`: does nothing at launch but return YES (0x100019134..0x100019218).
- `WarningViewController`: the storyboard's entry point; the earphone warning (section 9).
- A navigation controller with its bar hidden, whose root is `HomeScreenViewController`, the menu (section 9).
- `GameViewController`: hosts the scene, shows the score and coin labels (section 10).
- `GameScene`: the game, an `SKScene` and `SKPhysicsContactDelegate`.
- `ResultViewController`: the game over screen, name entry and saving (section 11).
- `RankingViewController` and `TableCell`: the local and world rankings (section 12).
- `RankingCloud`: CloudKit's public database, for the world ranking (section 12).

The flow, from the storyboard (`analysis/data/nib_Main.txt`): Warning, then `WarningToMenu` (not animated) to
the menu; the menu's two buttons go to the game and to the ranking; the game goes `GameToResult` to the result
screen; Replay unwinds to the game (`unwindToGameSegue`), Menu unwinds to the menu (`unwindToHomeScreenSegue`).

---

## 2. The scene, the lanes and the player

- **The scene** comes from `GameScene.sks`: 750 by 1334, anchor (0.5, 0.5), so (0, 0) is the centre
  (`analysis/data/sks_GameScene.txt`). `GameViewController` loads it with `GameScene(fileNamed:)`, so the game
  goes through `initWithCoder:`, and sets `scaleMode` 1, aspect fill (0x100017c24, 0x100017c68).
  Below, W and H are the scene's width and height.
- **Three lanes**, at x = -0.3 W, 0 and +0.3 W: -225, 0 and 225 (lanes 0, 1 and 2, left to right).
  - The fields `positionLaneZero/One/Two` are set to -0.3, 0 and 0.3 (0x10001566c..0x10001568c, **checked**)
    but nothing reads them. Movement uses its own literal constants (0x10000fa10, 0x10000fcb8), and
    `positionFloat` (0x100014108) a table {-0.3, 0, 0.3} at 0x1000248c0, indexed by `actualPositionPlayer`.
- **The player** starts in lane 1 (`actualPositionPlayer` = 1, 0x10001569c, **checked**), at (0, -0.25 H),
  so y = -333.5 (0x10000be5c..0x10000be90).
  - A circle physics body of half its width; category 2, contact mask 6, collision mask 0 (0x10000bec8..0x10000c048).
  - `changeSpritePlayer(withTorch)` (0x10000c0c0): scale W x 0.0007; frames "player", "player2", "player3" with a
    torch, "sem_tocha_1/2/3" without; textures [1, 2, 3, 2] at 0.1 s a frame, forever (helper 0x100019778).
    It does nothing once the player is dead.
- **The scenery**: three sprites, `scenario0` the size of the scene at (0, 0), `scenario1` at (0, H) and
  `scenario2` at (0, 2H) as its children (0x100016a90..0x100016cf4). They scroll down (section 6).
- **The listener** is the player: `scene.listener = player` (0x100016a78). Every positional sound is heard
  from the player's position, so from its lane.
- `update:` is an empty `ret` (0x10001561c, **checked**): nothing runs per frame. All timing is SKActions and
  NSTimers.
- A snow emitter (`Snow.sks`) is created at (0, 0.5 H), z 25, and never added to the scene, so it never shows
  (0x100017058..0x100017110, **checked**).

---

## 3. Starting a game

`didMoveToView:` sets up the scene, the gestures, the sounds and the light, then calls `tutorial` (0x100016d4c).
- `tutorial` (0x10000dea8) speaks the tutorial line on the first three games only (section 8), then starts a
  one-shot NSTimer for `startGame`: **4.0 s** after speaking (0x10000e634), **2.0 s** when it does not speak
  (0x10000e0e0).
- `-[GameScene startGame]` (0x1000152e4, **checked**) calls the score loop (section 7), sets `blockPlayer` to
  false and calls `createObjectScene`, the first spawn.
- Initial values (all three initialisers alike, 0x100015620, 0x100015d58, 0x100017154): `speedMonster` 4.0
  (0x1000157bc), `falloffSize` 2.0 (0x100015ba0), `blockPlayer` true, `playerDead` false, `countObstacles` 1,
  `countSubObstacles` 1, `countObjectScene` 0, `objectHeight` 0, `positionLastObstacles` 0,
  `currentScenario` "cenarioPedra" (0x100015cdc), and every scenario sprite "cenarioPedra".

---

## 4. Input

Four gesture recognisers on the view, all with the scene as target (`didMoveToView:`):
- Swipe right (direction 1): `movePlayerRight` (0x100016e34).
- Swipe left (2): `movePlayerLeft` (0x100016ee8).
- Swipe up (4): `throwTorch` (0x100016f98).
- Tap: `movePlayerTap` (0x100016fc4).

**A tap** goes left or right by where it lands. `touchesBegan:withEvent:` stores the first touch's x, in the
view's points, in `positionX` (0x100010588); `movePlayerTap` (0x10000fff0) compares it with W / 4: greater goes
right, otherwise left (0x100010028..0x100010034). W / 4 is 187.5 scene units against a value in view points, so
the split falls at the screen's centre only on a 375-point-wide phone (**inferred** from the units).

**Moving** (`movePlayerRight` 0x10000f8e4, `movePlayerLeft` 0x10000fb90, mirror images):
- Returns at once if the player is dead. `blockPlayer` is not checked, so the player can change lanes during
  the tutorial, before the game starts.
- Into a free lane: `soundMovePlayer` (the dash, section 13), then the new lane.
- At the edge (right from lane 2, left from lane 0): `playSoundFileNamed("MovimentoProibido.wav")`, no dash
  (0x10000f988..0x10000f9d4, 0x10000fc14).
- Then, edge or not: `moveToX(lane x, 0.15 s)` on the player **and on the music node**, and
  `moveToX(lane x - 0.072 W, 0.15 s)` on the torch light (0x10000fa60..0x10000fb38).

**Throwing** is in section 7.

---

## 5. What comes down the cave

**The chain of slots** (`createObjectScene`, 0x10000c674). Each call makes one object, a "slot", that starts at
the top (y = 0.5 H) and moves down. When it reaches y = 0.33 H, its own action calls `createObjectScene` again
(`moveObstacleWithBorn`, 0x100013ae8). So one slot follows another, every 0.165 x `speedMonster` seconds:
0.66 s at the start.

With s = `countObjectScene`:
- **Every 4th slot (s mod 4 = 0) is an obstacle.**
  - A monster, except every 7th obstacle (`countObstacles` mod 7 = 0), which is a bat swarm instead
    (0x10000c750..0x10000c7a0). No randomness.
  - If `objectHeight` is 4, a companion comes with it: a coin, or every 4th companion a torch
    (`countSubObstacles` mod 4; 0x10000c7d8..0x10000c824); then `objectHeight` = 0. Otherwise
    `objectHeight` = `coinRandom`, 1 to 4.
- **The other slots** hold a coin, or every 4th such item a torch, when `countObstacles` mod 3 = 0 and
  `objectHeight` is 3 or less and s mod 4 equals `objectHeight` (0x10000c6d4..0x10000c8bc). Otherwise the slot
  is an empty, invisible sprite that only keeps the chain going (0x10000c8d0..0x10000c91c).
- After each slot: s goes up by 1, the light dims a step (`changeFalloffSize`, section 7), and **every 20th
  slot, if `speedMonster` is 2.0 or more, it gains -0.12** (0x10000c958..0x10000c9a0, **checked**). It reaches
  about 1.96 after 340 slots, and stays there (**inferred** arithmetic).
  `speedMonster` is a duration, the seconds an object takes from top to bottom: smaller is faster.

**Lanes**: `lineRandom` is `arc4random_uniform(3) + 1` (0x1000116b8). An obstacle re-rolls until it differs
from the last obstacle's lane, and stores its lane (`choiceObstacleLine`, 0x100011770); a coin re-rolls the same
way but does not store it (`choiceObstacleCoin`, 0x1000117f4), so a coin is never in the last obstacle's lane.

**The monster** (`createMonster`, 0x10000caf8): an animated sprite at (lane x, 0.5 H), scale W x 0.0013, its look
chosen by `currentScenario`: "cenarioPedra" rock (`monstroPedra`, `monstroPedra2-1`, `monstroPedra2`),
"cenarioAgua" crystal (`monstroCristal...`), "cenarioGelo" ice (`monstroGelo...`). The "2" names are animation
frames, not other monsters. Physics: a rectangle half its size, centred 22 below it (0x10000cc68, **checked**);
category **0**, contact mask 7.

**Bats** (`createBats`, 0x10000d1b8): `morcego1` animated through `morcego1/2/3`, scale W x 0.0009; category 1,
contact mask 7.

**A torch to pick up** (`createTorchObstacle`, 0x10000d578): `torchObstacle`, scale W x 0.0009, not lit;
category 6, contact mask 2.

**A coin** (`createCoin`, 0x10000d86c): `rockCoin`, `waterCoin` or `iceCoin` by scenario, scale W x 0.0008;
category 7, contact mask 3.

**Movement**:
- A slot: `moveToY(0.33 H, 0.165 x speed)`, the call that makes the next slot, `moveToY(-0.5 H, 0.835 x speed)`,
  removed (0x100013ae8..0x100013cb4). The whole height in `speedMonster` seconds.
- A companion: `moveToY(-0.5 H, speed)`, removed (`moveObstacle`, 0x100013d5c); it makes no next slot.

**The physics categories** are plain numbers, 0 to 7, not single bits, and the contact code compares them with
`==`: monster 0, bat 1, player 2, roar sensor 3, thrown torch 4, torch pickup 6, coin 7. Gravity is (0, 0)
(0x1000169c4), and every collision mask is 0, so nothing pushes anything.

---

## 6. The roar, and how you hear what is coming

**The roar sensor** (`createRoarSensor`, 0x10000c344) is an invisible sprite across the cave at y = 0.07 H, built
from the empty image name `""`; category 3, contact mask 1. Its size comes from SpriteKit's placeholder for a
missing image, scaled W x 0.007 by 0.005 (**inferred** size).
- A **monster** touching it plays the roar at the monster's position: `playMonsterRoarAtPoint:` (0x10000f69c)
  moves the `roar` node there and plays "Rugido.mp3" at **volume 3.0 if the monster's x equals the player's**
  (the same lane) **and 1.0 otherwise** (0x10000f738..0x10000f764, **checked**).
- A **bat** touching it plays "BatSound.wav" the same way, at **3.0 in your lane, 0.7 in another**
  (`playBatSoundAtPoint:`, 0x10000f7c4).
- The sensor is at 0.07 H and the player at -0.25 H, so the roar comes when the monster is about a third of the
  screen away (0.32 H): roughly 0.32 x `speedMonster` seconds before it reaches you, about 1.3 s at the start
  and 0.6 s at the fastest (**inferred** arithmetic; contact begins when the bodies' edges meet, a little
  earlier than the centres).
- Both nodes are positional, and the listener is the player, so the roar also comes from the monster's side.

**The coin's jingle** ("tilintar.aiff") is set up as a positional node but never played, and `moveCoinSound`,
which would have moved it with a coin, is never called. Coins are silent until picked up.

**The scenery scrolls** (`moveScenario`, 0x100011840): scenario0 moves to -2H in 2 x `speedMonster` seconds,
jumps back, and calls `putScenario` (which starts it again) and `changeScenario` (section 7).

---

## 7. The torch, the light, contacts and the score

**The light** (`createLight`, 0x100023740): an `SKLightNode` at the player, 0.072 W to the left and 0.09 W up (the
width, not the height), falloff 2.0; light colour (1.0, 0.745, 0.357), shadow (0.149, 0, 0, 0.5), ambient
(0.063, 0, 0, 0.5). Everything with lighting mask 1 is lit by it.

**The torch burns down** once per slot (`changeFalloffSize`, 0x100023a0c), so faster as the game speeds up:
- falloff under 3: +0.025, and the burning sound's volume -0.003
- falloff under 5: +0.07, and volume -0.0045
- then, at the limit: falloff 1000 (the light is effectively out), the player's torchless sprite, and the
  burning sound removed
- That is about 40 slots from 2 to 3 and 29 more to 5 (**inferred** arithmetic): about 69 slots, 45 s at the
  start, with one torch.

**Picking up a torch** (player and torch pickup touch; `playerDidCollideWithTorch:`, 0x1000137b8): "pegou_tocha.wav"
at 1.5, the burning sound starts again (`createBackgroundTorch`, fading in over 3 s), falloff back to 2.0, the
torch sprite.

**Throwing** (swipe up; `throwTorch`, 0x10001111c):
- Only while the falloff is under 5.0 and `blockPlayer` is false, so only with a torch in hand and the game
  started. Being dead is not checked.
- The burning sound stops; "lancar_tocha.wav" plays at 1.3.
- A torch sprite (`Layer1` to `Layer6`) starts just ahead of the player and flies to y = +H in
  0.5 x `speedMonster` seconds, with a copy of the light (`throwLightTorch`) flying with it; its body is a
  circle twice as wide as the sprite (category 4).
- The player's own light goes out (falloff 1000) and the sprite becomes torchless. **Throwing uses up the torch.**

**Contacts** (`didBeginContact:`, closure 0x100012984). Most pairs are tested in one order of the two bodies only,
so a contact that arrives the other way round is ignored (**inferred** consequence):
- **Monster or bat and the roar sensor**: the roar or the bats (section 6). Both orders tested.
- **Coin and player**: "plim_moeda.wav" at 0.2, the coin removed, **score +10 and coins +1**
  (`playerDidCollideWithCoin:playerP:`, 0x10001390c).
- **Thrown torch and monster**: "MonsterDead.mp3" at 0.7, the monster, the torch and its light removed, and the
  player's light stays out (`torchDidCollideWithObstacle:obstacleE:`, 0x1000133b8). **No points, and no death
  sprite.** If the monster was still at or above 0.4175 H, it makes the next slot itself, since its own action
  will not now reach 0.33 H.
- **Thrown torch and bat**: the bat is **not** killed and the torch flies on; the bat dodges in 0.3 s, to the
  centre if it was at a side, or to a random side if it was in the centre; it also prints to the console
  (`torchDidCollideWithBat:batB:`, 0x10001356c).
- **Torch pickup and player**: picking it up (above).
- **Monster or bat and player**: death (below).

**Death** (`obstacleDidCollideWithPlayer:obstacleE:`, 0x1000230c4):
- `playerDead` true; the score loop stops; "screamingMan.wav" plays; the player is replaced by a dead sprite
  where the monster was, by scenario: `deadPedra.png`, `deadCristal.png` (water), `deadGelo.png`.
- The light is switched off, every sound but the roar removed (`removeNodesSounds`), the scenery paused.
- After a one-shot NSTimer of **1.0 s**, `clear`: the view controller clears the scene and performs `GameToResult`
  (0x100022fc8, 0x100018034).

**The score**: +1 every 0.25 s while playing (an action keyed "upScore", started by `startGame`; 0x1000154a4,
0x100015554), so 4 a second, and +10 a coin. Killing a monster scores nothing. **The coins** are one count, +1 a
coin; `rockCoin`, `waterCoin` and `iceCoin` are only pictures.

**The scenarios** (`changeScenario`, 0x100011c20), checked each time the scenery loops:
- **Rock to water** once `countObjectScene` is at least **81** (**checked**, `cmp #0x51` at 0x100011c50):
  `currentScenario` "cenarioAgua", the coin counter's icon `coinCounterWater`, and the scenery changed through
  `cenarioPedraAgua` to `cenarioAgua`.
- **Water to ice** at **161** (**checked**, `cmp #0xa1` at 0x100012180): "cenarioGelo", `coinCounterIce`,
  through `cenarioAguaGelo`.
- Ice is the last. The speed does not change with the scenario; the monsters' look, the coins' look, the dead
  sprite and the counter's icon do.

---

## 8. Speech: the tutorial line

`tutorial` (0x10000dea8):
- Reads the device language (`Locale.current`, `NSLocaleLanguageCode`); if there is none, the forced cast
  crashes (`brk`, 0x10000e830).
- Reads `countTutorial` from UserDefaults (0x10000e000, **checked**). Above 2: no speech. Otherwise it speaks,
  then stores the count plus 1 (0x10000e5bc..0x10000e5f0). So the line is spoken on the first three games.
- Compares the language with "pt", "es", "zh", "ru", "fr"; anything else is English.
- Speaks through `AVSpeechSynthesizer`, with the voice and rate:
  - English, "en-US", rate 0.55: "You need to scape from a cave full of monsters on the way! When you hear the
    roar, swipe or tap to the other side!"
  - Portuguese, "pt-BR", 0.6: "Voce precisa fugir da caverna desviando dos monstros de pedra no caminho! Quando
    ouvir o rugido, deslize ou toque para um dos lados!"
  - Spanish, "es-ES", 0.6: "Usted necesita escapar de la cueva esquivando de los monstruos de piedra en el
    camino! Cuando se oye un ruido, deslice o toque hacia un lado"
  - Chinese, "zh-CN", 0.6 (0x10000e48c), Russian, "ru-RU", 0.5 (0x10000e6b0), French, "fr-FR", 0.5
    (0x10000e760): the texts are in `analysis/data/strings.txt` under `__ustring`.
- It speaks whether VoiceOver is on or not.

---

## 9. The earphone warning and the menu

**WarningViewController**:
- The label: "Coloque o fone para uma melhor experiência" when the language is "pt", otherwise "Put the
  earphone on for a better experience" (0x10000ea3c..0x10000eb5c). Two languages only.
- After a one-shot timer of **3.0 s**, or at once on a touch, `WarningToMenu` (0x10000e9f0, 0x10000ed94).

**HomeScreenViewController**:
- Two buttons, both storyboard segues with no code: **play** (to the game) and **score** (to the ranking). Their
  titles are in a 1-point font: invisible, but what VoiceOver reads.
- On load: if UserDefaults has no `rank`, it is set to five entries of "Player", "0"; `rankWorld` is set to the
  same five on every launch; `countTutorial` is set to 0 if missing (0x10001a00c..0x10001a334).
- No sound or speech of its own.

---

## 10. The game screen

**GameViewController** (its `viewDidLoad` body is 0x1000179c4, which replay runs again):
- The score and coin labels start at "0".
- When VoiceOver is running, the whole game view becomes one accessibility element with
  `UIAccessibilityTraitAllowsDirectInteraction`, so VoiceOver passes the swipes and taps through to the game
  (0x100017cd8..0x100017d54). The score label is hidden from VoiceOver in the storyboard.
- `scoreUpWithValue:` and `coinUpWithValue:` add to the numbers in the labels' text (0x100018390).
- `changeCoinCounterWithScenario:` sets the counter's icon (0x100018eb4, 0x100018f74); replay does not reset it.
- At game over, `prepareForSegue` passes the score and coins to the result screen (0x100018cb8, 0x100018d60).

---

## 11. The result screen and saving

**ResultViewController**:
- Shows the score and coins, a name field (at most 15 characters, 0x1000204a0), **Replay** and **Menu**.
- **The name** is guessed from the device's name (`checkName`): "iPad de X" or "iPhone de X" gives X, "X's iPad"
  or "X's iPhone" gives X, anything else "Insert name".
- **Both buttons save first** (`checkRank`, then the unwind):
  - The score is saved locally only if it beats the 5th of the 5 local entries (strictly).
  - "Insert name" is saved as "unnamed player"; an empty name saves nothing, silently.
  - The new entry goes in, sorted by score, best first, and the 6th is dropped; `rank` is stored.
  - It is also sent to the world ranking (section 12).

**The crash a 2016 player reported** ("it crashes when I lose and my score is not recorded") is in `checkName`,
which runs as the result screen loads, before anything is saved. It always moves 8 and then 10 characters into
the device's name, before comparing anything, and traps when the name is shorter
(0x10001c340, 0x10001c388, the helper 0x10001fbd0, `brk` at 0x10001fdc4; **checked**). So on any device whose
name was under 10 characters, such as plain "iPhone", every game over crashed, and no score was ever saved. A
second crash could follow in the world save (section 12).

---

## 12. The rankings

**Local**: five entries, "Name" and "Score" as strings, in UserDefaults under `rank`.

**World** (`RankingCloud`, CloudKit's public database, record type "Ranking", fields "Nome" and "Pontuacao"):
- Saving reads every record, sorts them, and compares the score with the 10th, or the 20th if there are more
  than 18; it traps when there are fewer than 10 records, or exactly 19 (0x10000ac58..0x10000aca0). Ties
  qualify. It saves the new record, then deletes the one it pushed out, matched by name and score.
- The ranking screen's **World** tab queries every record, with no sort or limit, sorts them and shows them.
- The world ranking cannot work in a port.

**RankingViewController**: a Local / World switch, a table of position, name and score, and a MENU button.

**UserDefaults keys**: `rank`, `rankWorld`, `countTutorial`. Nothing else is saved: not the coins, not a best
score.

---

## 13. Every sound

Each is an `SKAudioNode` made in the initialisers, in this order (0x1000157d8..0x100015b0c); positional unless
noted (SpriteKit's default), heard from the player.
- "Rugido.mp3", `roar`: a monster reaching the sensor; 3.0 in your lane, 1.0 elsewhere. Never removed.
- "BatSound.wav", `batSound`: bats reaching the sensor; 3.0 in your lane, 0.7 elsewhere.
- "tilintar.aiff", `coinTinkle`: never played.
- "plim_moeda.wav", `coinSound`: a coin picked up, 0.2.
- "pegou_tocha.wav", `getTorchSound`: a torch picked up, 1.5.
- "lancar_tocha.wav", `playTorchSound`: a torch thrown, 1.3.
- "tocha.wav", `backgroundTorch`: the torch burning, looped, fading in over 3 s to 1.0, a little quieter at each
  dimming step, removed when the torch is thrown or burns out.
- "SC.wav", `backgroundMusic`: the music, looped, at 0.2, placed at the player and moved with the player's lane
  changes.
- "dash.aiff", `movePlayerSound`: a lane change, 0.25.
- "MonsterDead.mp3", `deadMonster`: a monster killed, 0.7.
- One-shot sounds played by the scene: "MovimentoProibido.wav" (a move into the wall) and "screamingMan.wav"
  (death).

---

## 14. The original's bugs and oddities

Each is the original's behaviour, read from the code. Whether the port keeps or fixes each is the dev's decision,
to be recorded in `DIVERGENCES.md` when made.
- The result screen crashes on short device names (section 11); the world save can crash too (section 12).
- No boss, despite the 2016 update's description.
- Bats cannot be killed; a torch only makes them dodge, possibly into your lane.
- The coin's jingle never plays.
- The snow effect is never shown.
- Most contacts are tested in one order of the bodies only.
- A monster killed between 0.4175 H and 0.33 H removes itself before its action makes the next slot, which
  would stop spawning (**inferred** from the two heights).
- The tap's left or right split is right only on a 375-point-wide screen.
- Lane changes work before the game starts; a torch can be thrown after death.
- An empty name throws a score away silently; the local ranking needs a strictly better score, the world one a
  tie.
- `rankWorld` is reset to placeholders on every launch.
- The thrown torch's body is a circle twice the sprite's width.
- The English line says "scape"; the French has spelling mistakes.
