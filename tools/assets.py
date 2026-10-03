"""Read the images' sizes out of ``game/Assets.car``, the compiled asset catalogue.

SpriteKit sizes a sprite made with ``SKSpriteNode(imageNamed:)`` by its image, in points,
before the game's own ``setScale``; the physics bodies are built from those sizes, so the
contacts - the roar above all - depend on them (aidocks/project_port_plan.md, question 11).
The binary holds the scale factors; the images' sizes are only here.

The catalogue is Apple's BOM store, big-endian:

    header      "BOMStore", version, block count, index offset and length, vars offset
                and length
    index       a count, then (address, length) for every block id
    vars        a count, then (block id, name length, name): CARHEADER, RENDITIONS,
                FACETKEYS, KEYFORMAT, ...
    a tree      "tree", version, the block id of its first path, block size, path count
    a path      is-leaf (u16), count (u16), forward and backward path ids, then count
                pairs of (value block id, key block id); a branch's values are child paths

Every value in the RENDITIONS tree is one image at one scale, a CSI header,
little-endian: "ISTC", version, flags, width, height, scale factor (x100), pixel format,
colour space, then the modification time, layout (u16), a u16, and the file name, 128
bytes.  Width and height are in pixels; points are pixels / (scale / 100).  An image
packed into a shared sheet (layout 1003) still carries its own width and height here.

The names the code asks for (``"monstroPedra"``) are not the file names: they are the
FACETKEYS tree's keys.  Each facet's value is a hotspot (two u16), a count (u16) and that
many (attribute, value) u16 pairs, little-endian; attribute 17 is the identifier.  Every
rendition key is a list of u16 values in the order KEYFORMAT gives ("kfmt", version,
count, then that many attribute ids, little-endian), one of them the identifier.  So a
name finds its images by identifier.

Writes ``analysis/data/assets.txt``: every image by the name the code uses, with its
file, pixels, scale and points; and ``insidethecave/scene/image_sizes.py``, the same sizes
in points for the game, which never reads Assets.car itself (builds do not ship it).
Standard library only.  Run from the repository:  python tools/assets.py
"""
from __future__ import annotations

import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAR = os.path.join(ROOT, 'game', 'Assets.car')
OUT = os.path.join(ROOT, 'analysis', 'data', 'assets.txt')
MODULE = os.path.join(ROOT, 'insidethecave', 'scene', 'image_sizes.py')


class Bom:
    def __init__(self, data: bytes):
        if data[:8] != b'BOMStore':
            raise ValueError('not a BOM store')
        self.data = data
        (_ver, _nblocks, index_off, _index_len,
         vars_off, _vars_len) = struct.unpack('>IIIIII', data[8:32])
        count = struct.unpack('>I', data[index_off:index_off + 4])[0]
        self.blocks = [struct.unpack('>II', data[index_off + 4 + 8 * i:index_off + 12 + 8 * i])
                       for i in range(count)]
        self.vars = {}
        n = struct.unpack('>I', data[vars_off:vars_off + 4])[0]
        p = vars_off + 4
        for _ in range(n):
            bid, ln = struct.unpack('>IB', data[p:p + 5])
            self.vars[data[p + 5:p + 5 + ln].decode('ascii')] = bid
            p += 5 + ln

    def block(self, bid: int) -> bytes:
        addr, length = self.blocks[bid]
        return self.data[addr:addr + length]

    def tree(self, name: str):
        """Every (key bytes, value bytes) in a named tree, walking its leaves in order."""
        t = self.block(self.vars[name])
        if t[:4] != b'tree':
            raise ValueError('%s is not a tree' % name)
        path = struct.unpack('>I', t[8:12])[0]
        # down the first branch to the first leaf
        while True:
            p = self.block(path)
            is_leaf, count = struct.unpack('>HH', p[:4])
            if is_leaf:
                break
            path = struct.unpack('>I', p[12:16])[0]
        while path:
            p = self.block(path)
            _is_leaf, count, forward, _backward = struct.unpack('>HHII', p[:12])
            for i in range(count):
                value, key = struct.unpack('>II', p[12 + 8 * i:20 + 8 * i])
                yield self.block(key), self.block(value)
            path = forward


IDENTIFIER = 17


def _key_format(bom):
    kf = bom.block(bom.vars['KEYFORMAT'])
    if kf[:4] != b'tmfk':
        raise ValueError('KEYFORMAT is not "kfmt"')
    count = struct.unpack('<I', kf[8:12])[0]
    return [struct.unpack('<I', kf[12 + 4 * i:16 + 4 * i])[0] for i in range(count)]


def _facets(bom):
    """identifier -> the names that use it."""
    names = {}
    for key, value in bom.tree('FACETKEYS'):
        count = struct.unpack('<H', value[4:6])[0]
        for i in range(count):
            attr, val = struct.unpack('<HH', value[6 + 4 * i:10 + 4 * i])
            if attr == IDENTIFIER:
                names.setdefault(val, []).append(key.decode('utf-8', 'replace'))
    return names


def renditions(path: str = CAR):
    """Every image in the catalogue: (asset name, file name, width px, height px, scale).
    An image no name uses (the packed sheets themselves) has the asset name ''."""
    with open(path, 'rb') as f:
        bom = Bom(f.read())
    attrs = _key_format(bom)
    at = attrs.index(IDENTIFIER)
    facets = _facets(bom)
    out = []
    for key, value in bom.tree('RENDITIONS'):
        if value[:4] != b'ISTC':
            continue
        ident = struct.unpack('<%dH' % len(attrs), key[:2 * len(attrs)])[at]
        width, height, scale = struct.unpack('<III', value[12:24])
        filename = value[40:168].split(b'\0', 1)[0].decode('utf-8', 'replace')
        for name in facets.get(ident, ['']):
            out.append((name, filename, width, height, scale / 100.0))
    return out


def points(width, height, scale):
    s = scale or 1.0
    return width / s, height / s


def sizes(path: str = CAR):
    """Every asset name the code can ask for -> its size in points."""
    return {name: points(w, h, s) for name, _f, w, h, s in renditions(path) if name}


def main():
    rows = sorted(renditions(), key=lambda r: (r[0] == '', r[0].lower()))
    lines = ['Every image in game/Assets.car, by the name the code asks for (tools/assets.py).',
             'Pixels as stored; points = pixels / scale, which is what SKSpriteNode(imageNamed:)',
             'sizes a sprite by before the game\'s own setScale.  A name the catalogue does not',
             'hold, such as the roar sensor\'s "", is a missing image to SpriteKit.', '',
             '%-22s %-34s %11s %6s %13s' % ('name', 'file', 'pixels', 'scale', 'points')]
    for name, filename, w, h, s in rows:
        pw, ph = points(w, h, s)
        lines.append('%-22s %-34s %5d x %-5d %4.1fx %6g x %g'
                     % (name or '(no name)', filename, w, h, s, pw, ph))
    lines.append('')
    lines.append('%d images' % len(rows))
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    write_module(sizes())


def write_module(table):
    out = ['"""Every image\'s size in points, by the name the code asks for, read out of',
           'game/Assets.car by tools/assets.py.  Generated: rerun that tool, do not edit."""',
           '', 'SIZES = {']
    for name in sorted(table, key=str.lower):
        w, h = table[name]
        out.append('    %r: (%r, %r),' % (name, w, h))
    out.append('}')
    with open(MODULE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('wrote %s, %d names' % (os.path.relpath(MODULE, ROOT), len(table)))


if __name__ == '__main__':
    sys.exit(main())
