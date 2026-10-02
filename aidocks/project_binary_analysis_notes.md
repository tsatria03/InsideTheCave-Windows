---
name: project_binary_analysis_notes
description: "How to read game/InsideTheCave: a thin arm64 Mach-O, unencrypted, Swift 3 with stripped symbols. File offset = address - 0x100000000. The section map, what the Objective-C metadata does and does not give, and why the 32-bit Thumb tooling of the reference port will not work unchanged."
metadata:
  node_type: memory
  type: project
---

Checked on 2026-10-02 by parsing the load commands (read-only).

**The binary:** `game/InsideTheCave`, 267,728 bytes. A **thin arm64** Mach-O (magic `CF FA ED FE`, cputype `0x0100000C`), not a fat file and not armv7, although `Info.plist` lists `armv7` under `UIRequiredDeviceCapabilities`. **Unencrypted**: `LC_ENCRYPTION_INFO_64` has `cryptid = 0` (cryptoff 0x4000, size 0x28000), so the code can be read directly.

**Addresses.** `__TEXT` is mapped at vmaddr `0x100000000` from file offset 0, and `__DATA` at `0x10002C000` from file offset `0x2C000`. So **file offset = address - 0x100000000** for both. Every address cited in the code and the references is a VM address, written in full (`0x100012345`) or, once agreed, with the leading `0x1000` dropped; say which.

**Sections worth knowing:**
- `__text` 0x100005764, size 0x1E4AC (about 124 KB: the whole game)
- `__stubs` 0x100023C10, `__stub_helper` 0x1000240CC
- `__cstring` 0x100024EC0, size 0x2AC4 (the sound names, UI text, keys)
- `__ustring` 0x10002B750 (UTF-16 strings, likely the accented Spanish and Portuguese text)
- `__objc_methname` 0x100028DF8 (selector names)
- Swift 3 reflection metadata: `__swift3_typeref`, `__swift3_reflstr` (field names), `__swift3_fieldmd`, `__swift3_assocty`, `__swift3_capture`, `__swift2_proto`
- `__objc_classlist` 0x10002CB58, size 0x48: **9 classes**
- `__objc_selrefs` 0x100032270, size 0x630 (about 198 selector references)
- `__objc_classrefs` 0x100032908, `__objc_data` 0x100032A30, `__data` 0x1000334C8

**What the metadata gives.** The binary's strings name nine game classes, mangled as `_TtC13InsideTheCave<len><Name>`, which matches the count in `__objc_classlist` (not yet walked entry by entry): `GameScene`, `GameViewController`, `HomeScreenViewController`, `ResultViewController`, `RankingViewController`, `WarningViewController`, `TableCell`, `RankingCloud` and `AppDelegate`. Their Objective-C method lists hold only `@objc` and overridden methods, and their property names come through (`speedMonster`, `falloffSize`, `countObstacles`). Calls into SpriteKit, AVFoundation, UIKit, CloudKit and UserDefaults go through `objc_msgSend` and resolve by selector, as in an Objective-C game.

**What it does not give.** The Swift symbols are **stripped**: no `_TFC13InsideTheCave...` function names are left. Swift calls its own methods directly or through the class vtable, not `objc_msgSend`, so inside `GameScene` a call to `createMonster` shows as a plain `bl` to an address. Map those addresses to names through the Objective-C method lists (each `@objc` method's IMP) and the vtable in the class metadata.

**Tooling.** The reference port in the gitignored `user/` folder has Mach-O and disassembly tools written for **32-bit Thumb-2** (capstone `CS_MODE_THUMB`, 32-bit `class_ro_t`, first fat slice). They will not work unchanged: they need arm64 (`CS_ARCH_ARM64`), 64-bit Objective-C structures, and arm64's `adrp`/`add` and `adrp`/`ldr` pairs for resolving strings and selectors. Its UI row-table tools fit that game's screens only. Building arm64 versions into `tools/` is a developer task ([[project_dev_tasks]]).

**Why:** The address rule and the architecture decide whether every later reading of the binary lands on the right bytes.

**How to apply:** Before porting or "reproducing" any behaviour that hinges on one branch or constant, decode the raw instructions at `address - 0x100000000` ([[feedback_side_by_side]]). Strings and selector names suggest what the game does; only the code proves it.
