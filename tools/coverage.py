"""Prove the listings in analysis/disasm cover the whole of __text, and nothing twice.

It reads every ``dz_*.txt`` back and checks:

* every address in LC_FUNCTION_STARTS heads exactly one function
* every 4-byte word of __text, from its first byte to its last, is listed exactly once, as an
  instruction or as a ``.word`` capstone could not decode
* how many words are ``.word``, so any code that could not be decoded is counted and named

It prints the verdict and exits 0 only when nothing is missing or listed twice.

    python tools/coverage.py
"""
from __future__ import annotations

import os
import re

import macho

DISASM = os.path.join(macho.ROOT, 'analysis', 'disasm')
HEAD = re.compile(r'^//// (.+?)  0x([0-9a-f]+)\.\.0x([0-9a-f]+)')
LINE = re.compile(r'^  0x([0-9a-f]+)  (\S+)')


def main() -> int:
    m = macho.load()
    text = m.section('__text')
    starts = sorted(s for s in m.function_starts if s in text)
    heads: dict[int, int] = {}
    words: dict[int, int] = {}
    undecoded = []
    for name in sorted(os.listdir(DISASM)):
        if not (name.startswith('dz_') and name.endswith('.txt')):
            continue
        with open(os.path.join(DISASM, name), encoding='utf-8') as fh:
            for line in fh:
                h = HEAD.match(line)
                if h:
                    va = int(h.group(2), 16)
                    heads[va] = heads.get(va, 0) + 1
                    continue
                x = LINE.match(line)
                if x:
                    va = int(x.group(1), 16)
                    words[va] = words.get(va, 0) + 1
                    if x.group(2) == '.word':
                        undecoded.append((va, name))
    problems = []
    missing_heads = [s for s in starts if s not in heads]
    double_heads = [s for s, n in heads.items() if n > 1]
    extra_heads = [s for s in heads if s not in set(starts)]
    expected = range(text.addr, text.end, 4)
    missing = [va for va in expected if va not in words]
    double = [va for va, n in words.items() if n > 1]
    outside = [va for va in words if not text.addr <= va < text.end]
    for label, items in (('function starts with no listing', missing_heads),
                         ('functions listed twice', double_heads),
                         ('listings for addresses that are not function starts', extra_heads),
                         ('words of __text not listed', missing),
                         ('words listed twice', double),
                         ('listed addresses outside __text', outside)):
        if items:
            problems.append('%d %s, first 0x%x' % (len(items), label, sorted(items)[0]))
    print('__text 0x%x..0x%x: %d words, %d functions.' % (text.addr, text.end, len(expected), len(starts)))
    print('listed: %d words in %d functions.' % (len(words), len(heads)))
    if undecoded:
        print('%d words capstone could not decode, listed as .word: %s'
              % (len(undecoded), ', '.join('0x%x (%s)' % u for u in undecoded[:10])))
    else:
        print('every word decoded as an instruction.')
    if problems:
        print('NOT COMPLETE:')
        for p in problems:
            print('  ' + p)
        return 1
    print('COMPLETE: every function and every word of __text is listed exactly once.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
