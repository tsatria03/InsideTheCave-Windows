"""Name every function in Inside The Cave's code that the binary gives a way to name.

The Swift symbols are stripped, so the 575 functions in __text have no names of their own.  These are
given, in order of trust, and each name says where it came from:

1. ``objc``: an Objective-C method's implementation, from the class's method list: ``-[GameScene
   createMonster]``.  For a Swift class these are the ``@objc`` thunks the runtime calls.
2. ``thunk``: the Swift body a thunk calls.  A thunk does little but call its body, so when an
   Objective-C method calls exactly one of the game's own functions, that function is the method's
   Swift body: ``GameScene.createMonster``.  Swift calls its own methods there directly, so most of the
   game's real code is in these.
3. ``entry``: ``main``, from LC_MAIN.
4. ``caller``: a function only one named function calls or takes the address of, named after it.  A
   closure handed to SKAction.run is ``GameScene.createMonster~closure1``; a function it calls is
   ``GameScene.createMonster~call1``, numbered in the order they appear.  This repeats until no more can
   be named, so a closure's own helpers are named too.
5. ``does``: a function named for what it plainly does - a body that ends in a call to the superclass's
   ``dealloc`` or ``initWithCoder:`` (``GameScene.dealloc~body``), a type metadata accessor
   (``metadata SKAction``), a single jump to another function (``jump~GameScene.createMonster``) - and
   then step 4 again for what those call.
6. ``class``: a helper only one class's functions call, numbered: ``GameScene~shared3``.
7. ``data``: a function no code calls but a table in the data points to.  Inside a class's Swift
   metadata (from 80 bytes past the class object, where the field offsets and the vtable are, to the
   end its class size gives) it is ``GameScene.vtable[k]``, k counting 8-byte slots from there; in any
   other run of pointers to functions it is ``table@0x<run start>[k]`` (a value or protocol witness
   table, most likely).  Relative pointers in __TEXT,__const count too.  Then steps 4 and 6 again.
8. the rest are ``fn_<address>``, with the functions that call them, in analysis/data/functions.txt.

    python tools/names.py          writes analysis/data/functions.txt
"""
from __future__ import annotations

import os

import macho
import dz

OUT = os.path.join(macho.ROOT, 'analysis', 'data', 'functions.txt')
#: A thunk is short; anything longer that calls one game function is a method in its own right.
THUNK_MAX = 48


def swift_name(class_name: str, selector: str) -> str:
    """'GameScene', 'torchDidCollideWithBat:batB:' -> 'GameScene.torchDidCollideWithBat:batB:'."""
    return '%s.%s' % (class_name, selector)


class Graph:
    """Who calls whom, and who takes whose address, across every function."""

    def __init__(self, d: dz.Disassembler):
        self.d = d
        self.calls: dict[int, list[int]] = {}      # function -> game functions it calls, in order
        self.refs: dict[int, list[int]] = {}       # function -> functions whose address it takes
        self.length: dict[int, int] = {}
        for start in d.starts:
            calls, refs = [], []
            insns = d.function(start)
            self.length[start] = len(insns)
            for x in insns:
                if x.kind in ('call', 'jump') and x.target is not None and x.target in d.starts \
                        and x.target != start:
                    calls.append(x.target)
                if x.ref is not None and x.ref in d.starts and x.ref != start:
                    refs.append(x.ref)
            self.calls[start] = calls
            self.refs[start] = refs

    def callers(self) -> dict[int, set[int]]:
        found: dict[int, set[int]] = {}
        for f, targets in list(self.calls.items()) + list(self.refs.items()):
            for t in targets:
                found.setdefault(t, set()).add(f)
        return found


def compute(d: dz.Disassembler = None):
    """{address: (name, how it was named)} for every function start."""
    d = d or dz.Disassembler()
    m = d.m
    names: dict[int, tuple[str, str]] = {}
    d.names = {}
    imps = m.methods_by_imp()
    for imp, (c, meth) in imps.items():
        names[imp] = (meth.name(c.name), 'objc')
    if m.entry in d.starts:
        names[m.entry] = ('main', 'entry')
    graph = Graph(d)
    # the Swift bodies behind the thunks
    for imp, (c, meth) in imps.items():
        if imp not in d.starts:
            continue
        inside = [t for t in dict.fromkeys(graph.calls[imp]) if t not in imps]
        if len(inside) == 1 and graph.length[imp] <= THUNK_MAX and inside[0] not in names:
            names[inside[0]] = (swift_name(c.name, meth.selector), 'thunk of ' + meth.name(c.name))
    _by_caller(d, graph, names)
    _by_what_it_does(d, graph, names)
    _by_caller(d, graph, names)
    _by_class(d, graph, names)
    _by_data(d, names)
    _by_caller(d, graph, names)
    _by_class(d, graph, names)
    for f in d.starts:
        if f not in names:
            names[f] = ('fn_%x' % f, '')
    return names, graph


def _by_caller(d, graph, names):
    """Closures and helpers, named after their one caller, until nothing more can be named."""
    changed = True
    while changed:
        changed = False
        callers = graph.callers()
        counters: dict[tuple[int, str], int] = {}
        for f in d.starts:
            if f not in names:
                continue
            for kind, targets in (('call', graph.calls[f]), ('closure', graph.refs[f])):
                for t in dict.fromkeys(targets):
                    if t in names:
                        continue
                    who = callers.get(t, set())
                    if who == {f}:
                        n = counters.get((f, kind), 0) + 1
                        counters[(f, kind)] = n
                        names[t] = ('%s~%s%d' % (names[f][0], kind, n), 'only caller ' + names[f][0])
                        changed = True


def _by_what_it_does(d, graph, names):
    """Name the unnamed functions whose instructions say plainly what they are."""
    d.names = {va: n for va, (n, _how) in names.items()}
    taken = {n for n, _how in names.values()}

    def give(f, name, how):
        base, k = name, 2
        while name in taken:
            name = '%s#%d' % (base, k)
            k += 1
        taken.add(name)
        names[f] = (name, 'does: ' + how)

    for f in d.starts:
        if f in names:
            continue
        insns = d.function(f)
        notes = [n for x in insns for n in x.notes]
        supers = [n[len('super '):] for n in notes if n.startswith('super ')]
        sent_super = [n.split('[? ')[1].rstrip(']') for n in notes
                      if n.startswith('_objc_msgSendSuper2') and '[? ' in n]
        classes = [n[len('class '):] for n in notes if n.startswith('class ')]
        calls = [n for x in insns if x.kind in ('call', 'jump') for n in x.notes]
        if supers and sent_super:
            give(f, '%s.%s~body' % (supers[0], sent_super[-1]),
                 'ends in [super %s] of %s' % (sent_super[-1], supers[0]))
        elif any(c.startswith(('_swift_getObjCClassMetadata', '_swift_getInitializedObjCClass'))
                 for c in calls) and classes:
            give(f, 'metadata %s' % classes[0], 'swift type metadata accessor for %s' % classes[0])
        elif len(insns) == 1 and insns[0].kind == 'jump' and insns[0].notes:
            give(f, 'jump~%s' % insns[0].notes[0].split('  ')[0], 'a single jump')
        elif len(insns) == 1 and insns[0].mnemonic == 'ret':
            give(f, 'empty~%x' % f, 'a single ret')


#: Sections that never hold pointers to code.
NOT_POINTERS = {'__bss', '__common', '__text', '__stubs', '__stub_helper', '__cstring', '__objc_methname',
                '__ustring', '__unwind_info', '__swift3_reflstr', '__swift3_typeref'}


def data_references(m, starts) -> dict[int, list[tuple[str, int]]]:
    """Every function start a data section points to: {function: [(section, slot address), ...]}.
    Absolute 8-byte pointers anywhere, and 32-bit relative ones in __TEXT."""
    import struct
    starts = set(starts)
    found: dict[int, list[tuple[str, int]]] = {}
    for s in m.sections:
        if s.sectname in NOT_POINTERS or not s.size:
            continue
        data = m.read(s.addr, s.size)
        for i in range(0, len(data) - 7, 8):
            v = struct.unpack_from('<Q', data, i)[0]
            if v in starts:
                found.setdefault(v, []).append((s.sectname, s.addr + i))
        if s.segname == '__TEXT':
            for i in range(0, len(data) - 3, 4):
                v = s.addr + i + struct.unpack_from('<i', data, i)[0]
                if v in starts:
                    found.setdefault(v, []).append((s.sectname + ' (relative)', s.addr + i))
    return found


def _by_data(d, names):
    m = d.m
    starts = set(d.starts)
    refs = data_references(m, d.starts)
    spans = []
    for c in m.classes:
        address_point, class_size = m.u32(c.address + 60), m.u32(c.address + 56)
        spans.append((c.address + 80, c.address - address_point + class_size, c.name))
    taken = {n for n, _how in names.values()}
    for f in d.starts:
        if f in names or f not in refs:
            continue
        section, slot = refs[f][0]
        span = next(((lo, hi, cls) for lo, hi, cls in spans if lo <= slot < hi), None)
        if span:
            lo, _hi, cls = span
            name, how = '%s.vtable[%d]' % (cls, (slot - lo) // 8), \
                'data: slot 0x%x in the Swift metadata of %s' % (slot, cls)
        else:
            run = slot
            if 'relative' not in section:
                while m.mapped(run - 8) and m.u64(run - 8) in starts:
                    run -= 8
            step = 4 if 'relative' in section else 8
            name, how = 'table@0x%x[%d]' % (run, (slot - run) // step), \
                'data: slot 0x%x in %s' % (slot, section)
        while name in taken:
            name += "'"
        taken.add(name)
        names[f] = (name, how)


def _by_class(d, graph, names):
    """A helper every caller of which belongs to one class: that class's shared helper."""
    classes = {c.name for c in d.m.classes}

    def owner(name):
        head = name[2:].split(' ')[0] if name.startswith(('-[', '+[')) else name.split('~')[0].split('.')[0]
        return head if head in classes else None

    callers = graph.callers()
    counters: dict[str, int] = {}
    for f in d.starts:
        if f in names:
            continue
        owners = {owner(names[c][0]) for c in callers.get(f, ()) if c in names}
        if len(owners) == 1 and None not in owners:
            cls = owners.pop()
            counters[cls] = counters.get(cls, 0) + 1
            names[f] = ('%s~shared%d' % (cls, counters[cls]),
                        'class: called only from %s' % cls)


def load_names(d: dz.Disassembler) -> dict[int, str]:
    names, _graph = compute(d)
    d.names = {va: n for va, (n, _how) in names.items()}
    return d.names


def write(names, graph, d) -> None:
    callers = graph.callers()
    lines = ['Every function in __text, by address',
             'Generated by tools/names.py.  How each was named: objc (its Objective-C method), thunk (the',
             'Swift body its @objc thunk calls), entry (LC_MAIN), only caller (a closure or helper named after',
             'the one function that calls it or takes its address), or unnamed (fn_<address>, with its callers).',
             '']
    for f in d.starts:
        name, how = names[f]
        _, end = d.bounds(f)
        line = '0x%x  %5d bytes  %s' % (f, end - f, name)
        if how:
            line += '    (%s)' % how
        else:
            who = sorted(callers.get(f, ()))
            if who:
                line += '    (called by %s)' % ', '.join(names[w][0] for w in who[:6]) + \
                        (' and %d more' % (len(who) - 6) if len(who) > 6 else '')
            else:
                line += '    (no caller found in the code)'
        lines.append(line)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')


def main() -> int:
    d = dz.Disassembler()
    names, graph = compute(d)
    write(names, graph, d)
    counts: dict[str, int] = {}
    for _n, how in names.values():
        key = how.split(' ')[0].rstrip(':') if how else 'unnamed'
        key = {'only': 'caller'}.get(key, key)
        counts[key] = counts.get(key, 0) + 1
    print('wrote analysis/data/functions.txt: %d functions - %s'
          % (len(names), ', '.join('%d %s' % (v, k) for k, v in sorted(counts.items()))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
