# tools

The tools that disassemble Inside The Cave's iOS binary into `analysis/`. They only read the binary
and the app bundle, and only write into `analysis/`; none of them runs or plays anything.

They need Python 3.12 or newer and, for the disassembly, `capstone` (`pip install capstone`).
Capstone is never needed to play or build the game, so it is not in `requirements.txt`.
`macho.py`, `classes.py` and `archive.py` use the standard library only.

## The binary

`game/InsideTheCave` is a thin **arm64** Mach-O, unencrypted (`cryptid = 0`), written in Swift 3 with
SpriteKit, its Swift symbols stripped. `tools/classes.py` copies it to
`analysis/bin/InsideTheCave_arm64`, which the tools read first, so the analysis can be redone from
`analysis/` alone. `INSIDETHECAVE_BINARY` points them at another copy.

Every address in the tools' output, in the code and in `aidocks/` is a **VM address**. `__TEXT` is
mapped at `0x100000000` from file offset 0 and `__DATA` at `0x10002C000` from `0x2C000`, so
**file offset = address - 0x100000000**.

## Running everything

```
python tools/classes.py      # analysis/bin, analysis/data/classes.json and classes.txt
python tools/names.py        # analysis/data/functions.txt
python tools/listings.py     # analysis/disasm/dz_<Class>.txt (also rewrites functions.txt)
python tools/coverage.py     # proves the listings cover all of __text, once each
python tools/strings.py      # analysis/data/strings.txt
python tools/archive.py      # the scenes, storyboards, Info.plist and asset names
```

Each takes a second or two. `coverage.py` exits 0 only when every function and every 4-byte word
of `__text` is listed exactly once.

## The tools

- **`macho.py`**: the library the rest import. Load commands, segments and sections; the symbol
  table, indirect symbols and dyld's bind opcodes, which name every stub, pointer slot and external
  class; `LC_FUNCTION_STARTS`; the 64-bit Objective-C classes, methods, instance variables (and the
  globals Swift reads their offsets from), properties and references; the C and UTF-16 strings; and
  Swift 3's field metadata, whose 12-byte descriptor (no superclass pointer) was read from the bytes.
  `python tools/macho.py` prints a summary.
- **`classes.py`**: the nine classes, their superclasses, fields with offsets and Swift types, and
  every method's implementation address.
- **`dz.py`**: capstone disassembly, annotated by following the registers on the straight path into
  each instruction: strings, selectors with their receivers, classes, imports, closures, `mov`/`movk`
  constants with the double their bits make, constant-pool floats, and the stored property each load
  or store reaches. `python tools/dz.py 0x100015620`, an address range, or a name such as
  `"GameScene.createMonster"`.
- **`names.py`**: names the functions the binary gives a way to name, and says how: Objective-C
  methods, the Swift bodies behind their `@objc` thunks, closures and helpers after their only caller,
  bodies of `super` calls, metadata accessors, trampolines, class-only helpers, and vtable and witness
  table entries found through the data. The rest stay `fn_<address>`, listed with their callers.
- **`listings.py`**: writes every function, one file per class, with its name, bounds, how it was
  named and who calls it.
- **`coverage.py`**: the check that the disassembly is complete.
- **`strings.py`**: every string, with the functions that load it.
- **`archive.py`**: decodes the SpriteKit scenes (NSKeyedArchiver plists), the compiled storyboards
  (Apple's NIBArchive format), `Info.plist`, and the names in `Assets.car`.

## Reading the listings

- The annotations after `;` are hints. The register following forgets everything at a branch target
  and after a call, so it is right on the straight path and silent elsewhere. Check the instructions
  themselves before relying on one for a port.
- In a Swift method body (`GameScene.createMonster`), `self` is in `x20`; in an `@objc` thunk
  (`-[GameScene createMonster]`) it is in `x0`. Floating-point arguments are in `d0` to `d7`, and
  `CGFloat` is a `Double`.
- `~closureN` is a closure the function takes the address of, usually a block for `SKAction.run`;
  `~callN` is a helper only that function calls.
