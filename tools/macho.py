"""Read the arm64 Mach-O of Inside The Cave: the library every other tool imports.

``game/InsideTheCave`` is a thin arm64 executable, unencrypted, built with Xcode 8.2 in Swift 3.  This
reads everything the disassembly needs out of it, with the standard library only:

* the load commands, segments and sections, and the address rule: ``__TEXT`` is mapped at
  0x100000000 from file offset 0, so a file offset is the address minus 0x100000000
* the symbol table, the indirect symbols (which name each ``__stubs`` entry and each ``__got`` and
  ``__la_symbol_ptr`` slot) and dyld's bind opcodes (which name the external classes the game's own
  classes and class references point to, such as ``_OBJC_CLASS_$_SKScene``)
* ``LC_FUNCTION_STARTS``, the start of every function in ``__text``, and ``LC_DATA_IN_CODE``
* the 64-bit Objective-C metadata: the class list, each class's metaclass, superclass, instance
  variables (with their offsets), properties and methods (with their implementations), and the
  selector, class and superclass references
* the C strings and the UTF-16 strings
* Swift 3's reflection metadata: each type's stored fields, by name and mangled type

Every address here is a VM address.  Nothing here runs or writes anything.
"""
from __future__ import annotations

import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
#: The binary the tools read: the copy kept in analysis/bin, or failing that the app bundle's own.
BINARY_CANDIDATES = (os.path.join(ROOT, 'analysis', 'bin', 'InsideTheCave_arm64'),
                     os.path.join(ROOT, 'game', 'InsideTheCave'))
#: Where the tools' environment variable can point at another copy.
BINARY_ENV = 'INSIDETHECAVE_BINARY'

MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C

LC_SEGMENT_64 = 0x19
LC_SYMTAB = 0x2
LC_DYSYMTAB = 0xB
LC_LOAD_DYLIB = 0xC
LC_LOAD_WEAK_DYLIB = 0x80000018
LC_DYLD_INFO = 0x22
LC_DYLD_INFO_ONLY = 0x80000022
LC_FUNCTION_STARTS = 0x26
LC_DATA_IN_CODE = 0x29
LC_ENCRYPTION_INFO_64 = 0x2C
LC_MAIN = 0x80000028

INDIRECT_SYMBOL_LOCAL = 0x80000000
INDIRECT_SYMBOL_ABS = 0x40000000

#: The kinds an LC_DATA_IN_CODE entry can have.
DICE_KINDS = {1: 'data', 2: 'jump table 8', 3: 'jump table 16', 4: 'jump table 32', 5: 'abs jump table 32'}


def binary_path() -> str:
    """The binary to read: INSIDETHECAVE_BINARY, then analysis/bin/InsideTheCave_arm64, then
    game/InsideTheCave."""
    named = os.environ.get(BINARY_ENV)
    if named:
        return named
    for path in BINARY_CANDIDATES:
        if os.path.isfile(path):
            return path
    raise SystemExit('the binary was not found: looked in %s' % ', '.join(BINARY_CANDIDATES))


def _uleb(data: bytes, i: int):
    value = shift = 0
    while True:
        byte = data[i]
        i += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, i


def _sleb(data: bytes, i: int):
    value = shift = 0
    while True:
        byte = data[i]
        i += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            if byte & 0x40:
                value -= 1 << shift
            return value, i


class Section:
    __slots__ = ('segname', 'sectname', 'addr', 'size', 'offset', 'flags', 'reserved1', 'reserved2')

    def __init__(self, segname, sectname, addr, size, offset, flags, reserved1, reserved2):
        self.segname, self.sectname = segname, sectname
        self.addr, self.size, self.offset = addr, size, offset
        self.flags, self.reserved1, self.reserved2 = flags, reserved1, reserved2

    @property
    def end(self) -> int:
        return self.addr + self.size

    def __contains__(self, va: int) -> bool:
        return self.addr <= va < self.end

    def __repr__(self):
        return '<%s,%s 0x%x..0x%x>' % (self.segname, self.sectname, self.addr, self.end)


class Segment:
    __slots__ = ('name', 'vmaddr', 'vmsize', 'fileoff', 'filesize', 'sections')

    def __init__(self, name, vmaddr, vmsize, fileoff, filesize):
        self.name, self.vmaddr, self.vmsize = name, vmaddr, vmsize
        self.fileoff, self.filesize = fileoff, filesize
        self.sections = []


class ObjCMethod:
    __slots__ = ('selector', 'types', 'imp', 'meta')

    def __init__(self, selector, types, imp, meta):
        self.selector, self.types, self.imp, self.meta = selector, types, imp, meta

    def name(self, class_name: str) -> str:
        return '%s[%s %s]' % ('+' if self.meta else '-', class_name, self.selector)


class ObjCClass:
    """One class from __objc_classlist: its names, its superclass, and its lists."""

    def __init__(self):
        self.address = 0
        self.raw_name = ''           # as the runtime knows it: _TtC13InsideTheCave9GameScene
        self.name = ''               # demangled for reading: GameScene
        self.superclass = ''         # a name: another of the game's classes, or SKScene and the like
        self.metaclass = 0
        self.flags = 0
        self.instance_size = 0
        self.methods: list[ObjCMethod] = []
        self.ivars: list[tuple[int, str, str, int]] = []      # (offset, name, type, size)
        #: Where each ivar's offset is kept: Swift reads a stored property of a class with an Objective-C
        #: ancestor through this global, so a load from it names the field.  (address -> ivar name)
        self.ivar_offset_slots: dict[int, str] = {}
        self.properties: list[tuple[str, str]] = []           # (name, attributes)
        self.protocols: list[str] = []
        self.swift = False

    def __repr__(self):
        return '<class %s : %s>' % (self.name, self.superclass)


def demangle_class(raw: str) -> str:
    """'_TtC13InsideTheCave9GameScene' -> 'GameScene'.  Only the plain Swift class form is taken apart;
    anything else comes back as it was."""
    if raw.startswith('_TtC'):
        rest = raw[4:]
        parts = []
        while rest and rest[0].isdigit():
            n = 0
            while rest and rest[0].isdigit():
                n = n * 10 + int(rest[0])
                rest = rest[1:]
            parts.append(rest[:n])
            rest = rest[n:]
        if len(parts) >= 2 and not rest:
            return parts[-1]
    return raw


class MachO:
    """The whole binary, parsed once."""

    def __init__(self, path: str = None):
        self.path = path or binary_path()
        with open(self.path, 'rb') as fh:
            self.data = fh.read()
        self.segments: list[Segment] = []
        self.sections: list[Section] = []
        self.dylibs: list[str] = []
        self.symbols: list[tuple[str, int, int, int]] = []    # (name, type, sect, value)
        self.indirect: list[int] = []
        self.function_starts: list[int] = []
        self.data_in_code: list[tuple[int, int, str]] = []    # (address, length, kind)
        self.binds: dict[int, str] = {}                       # slot address -> symbol
        self.lazy_binds: dict[int, str] = {}
        self.entry = None
        self.cryptid = None
        self._dyld_info = None
        self._parse()
        self.stubs = self._indirect_slots('__stubs')
        self.got = self._indirect_slots('__got')
        self.lazy_pointers = self._indirect_slots('__la_symbol_ptr')
        self._parse_binds()
        self.selrefs = self._pointer_section('__objc_selrefs', self.cstr)
        self.classes = self._parse_classes()
        self.class_by_address = {c.address: c for c in self.classes}
        self.classrefs = self._pointer_section('__objc_classrefs', self.class_name_at)
        self.superrefs = self._pointer_section('__objc_superrefs', self.class_name_at)

    # ---- raw reading ------------------------------------------------------------------------------

    def offset(self, va: int) -> int:
        """The file offset of a VM address, through the segment that maps it."""
        for seg in self.segments:
            if seg.vmaddr <= va < seg.vmaddr + seg.filesize:
                return va - seg.vmaddr + seg.fileoff
        raise ValueError('0x%x is not in the file' % va)

    def mapped(self, va: int) -> bool:
        return any(seg.vmaddr <= va < seg.vmaddr + seg.filesize for seg in self.segments)

    def read(self, va: int, size: int) -> bytes:
        off = self.offset(va)
        return self.data[off:off + size]

    def u16(self, va): return struct.unpack_from('<H', self.data, self.offset(va))[0]
    def u32(self, va): return struct.unpack_from('<I', self.data, self.offset(va))[0]
    def s32(self, va): return struct.unpack_from('<i', self.data, self.offset(va))[0]
    def u64(self, va): return struct.unpack_from('<Q', self.data, self.offset(va))[0]
    def f32(self, va): return struct.unpack_from('<f', self.data, self.offset(va))[0]
    def f64(self, va): return struct.unpack_from('<d', self.data, self.offset(va))[0]

    def cstr(self, va: int) -> str:
        off = self.offset(va)
        end = self.data.index(b'\0', off)
        return self.data[off:end].decode('utf-8', 'replace')

    def section(self, sectname: str, segname: str = None) -> Section | None:
        for sect in self.sections:
            if sect.sectname == sectname and (segname is None or sect.segname == segname):
                return sect
        return None

    def section_of(self, va: int) -> Section | None:
        for sect in self.sections:
            if va in sect:
                return sect
        return None

    # ---- load commands ----------------------------------------------------------------------------

    def _parse(self):
        magic, cputype, _sub, _filetype, ncmds, _sizeofcmds, _flags, _res = struct.unpack_from(
            '<IiiIIIII', self.data, 0)
        if magic != MH_MAGIC_64 or cputype != CPU_TYPE_ARM64:
            raise SystemExit('%s is not a thin arm64 Mach-O (magic 0x%x, cputype 0x%x)'
                             % (self.path, magic, cputype))
        p = 32
        for _ in range(ncmds):
            cmd, size = struct.unpack_from('<II', self.data, p)
            if cmd == LC_SEGMENT_64:
                name = self.data[p + 8:p + 24].rstrip(b'\0').decode()
                vmaddr, vmsize, fileoff, filesize = struct.unpack_from('<QQQQ', self.data, p + 24)
                nsects = struct.unpack_from('<I', self.data, p + 64)[0]
                seg = Segment(name, vmaddr, vmsize, fileoff, filesize)
                for j in range(nsects):
                    q = p + 72 + j * 80
                    sectname = self.data[q:q + 16].rstrip(b'\0').decode()
                    segname = self.data[q + 16:q + 32].rstrip(b'\0').decode()
                    addr, ssize = struct.unpack_from('<QQ', self.data, q + 32)
                    offset, _align, _reloff, _nreloc, flags, r1, r2 = struct.unpack_from(
                        '<IIIIIII', self.data, q + 48)
                    sect = Section(segname, sectname, addr, ssize, offset, flags, r1, r2)
                    seg.sections.append(sect)
                    self.sections.append(sect)
                self.segments.append(seg)
            elif cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB):
                name_off = struct.unpack_from('<I', self.data, p + 8)[0]
                end = self.data.index(b'\0', p + name_off)
                self.dylibs.append(self.data[p + name_off:end].decode())
            elif cmd == LC_SYMTAB:
                symoff, nsyms, stroff, _strsize = struct.unpack_from('<IIII', self.data, p + 8)
                for k in range(nsyms):
                    strx, ntype, nsect, _ndesc, value = struct.unpack_from('<IBBHQ', self.data,
                                                                           symoff + k * 16)
                    end = self.data.index(b'\0', stroff + strx)
                    name = self.data[stroff + strx:end].decode('utf-8', 'replace')
                    self.symbols.append((name, ntype, nsect, value))
            elif cmd == LC_DYSYMTAB:
                indirectoff, nindirect = struct.unpack_from('<II', self.data, p + 56)
                self.indirect = list(struct.unpack_from('<%dI' % nindirect, self.data, indirectoff))
            elif cmd in (LC_DYLD_INFO, LC_DYLD_INFO_ONLY):
                self._dyld_info = struct.unpack_from('<10I', self.data, p + 8)
            elif cmd == LC_FUNCTION_STARTS:
                off, size_ = struct.unpack_from('<II', self.data, p + 8)
                self._function_starts_blob = (off, size_)
            elif cmd == LC_DATA_IN_CODE:
                off, size_ = struct.unpack_from('<II', self.data, p + 8)
                for k in range(size_ // 8):
                    fileoff, length, kind = struct.unpack_from('<IHH', self.data, off + k * 8)
                    self.data_in_code.append((fileoff, length, DICE_KINDS.get(kind, str(kind))))
            elif cmd == LC_MAIN:
                self.entry = struct.unpack_from('<Q', self.data, p + 8)[0]
            elif cmd == LC_ENCRYPTION_INFO_64:
                self.cryptid = struct.unpack_from('<I', self.data, p + 16)[0]
            p += size
        text = self.segment('__TEXT')
        # data-in-code entries are file offsets; keep them as addresses
        self.data_in_code = [(off - text.fileoff + text.vmaddr, length, kind)
                             for off, length, kind in self.data_in_code]
        if self.entry is not None:
            self.entry += text.vmaddr
        if hasattr(self, '_function_starts_blob'):
            off, size_ = self._function_starts_blob
            blob = self.data[off:off + size_]
            addr, i = text.vmaddr, 0
            while i < len(blob):
                delta, i = _uleb(blob, i)
                if delta == 0:
                    break
                addr += delta
                self.function_starts.append(addr)

    def segment(self, name: str) -> Segment | None:
        return next((s for s in self.segments if s.name == name), None)

    # ---- imports ----------------------------------------------------------------------------------

    def _indirect_slots(self, sectname: str) -> dict[int, str]:
        """Each entry of a stubs or pointer section, by address, named through the indirect symbols."""
        sect = self.section(sectname)
        if sect is None:
            return {}
        width = sect.reserved2 if sectname == '__stubs' else 8
        found = {}
        for k in range(sect.size // width):
            index = self.indirect[sect.reserved1 + k]
            if index & (INDIRECT_SYMBOL_LOCAL | INDIRECT_SYMBOL_ABS):
                name = '<local>'
            else:
                name = self.symbols[index][0]
            found[sect.addr + k * width] = name
        return found

    def _parse_binds(self):
        if not self._dyld_info:
            return
        (_rebase_off, _rebase_size, bind_off, bind_size, weak_off, weak_size,
         lazy_off, lazy_size, _export_off, _export_size) = self._dyld_info
        self._run_binds(bind_off, bind_size, self.binds, lazy=False)
        self._run_binds(weak_off, weak_size, self.binds, lazy=False)
        self._run_binds(lazy_off, lazy_size, self.lazy_binds, lazy=True)

    def _run_binds(self, off, size, into, lazy):
        data = self.data[off:off + size]
        i = 0
        symbol = ''
        seg_index = 0
        addr = 0
        while i < len(data):
            byte = data[i]
            i += 1
            op, imm = byte & 0xF0, byte & 0x0F
            if op == 0x00:                                  # DONE; separates lazy entries
                if not lazy:
                    break
            elif op in (0x10, 0x30):                        # dylib ordinal, immediate or special
                pass
            elif op == 0x20:
                _, i = _uleb(data, i)
            elif op == 0x40:                                # symbol name
                end = data.index(b'\0', i)
                symbol = data[i:end].decode('utf-8', 'replace')
                i = end + 1
            elif op == 0x50:                                # type
                pass
            elif op == 0x60:
                _, i = _sleb(data, i)
            elif op == 0x70:                                # segment and offset
                seg_index = imm
                value, i = _uleb(data, i)
                addr = self.segments[seg_index].vmaddr + value
            elif op == 0x80:
                value, i = _uleb(data, i)
                addr = (addr + value) & 0xFFFFFFFFFFFFFFFF
            elif op == 0x90:
                into[addr] = symbol
                addr += 8
            elif op == 0xA0:
                into[addr] = symbol
                value, i = _uleb(data, i)
                addr = (addr + 8 + value) & 0xFFFFFFFFFFFFFFFF
            elif op == 0xB0:
                into[addr] = symbol
                addr += 8 + imm * 8
            elif op == 0xC0:
                count, i = _uleb(data, i)
                skip, i = _uleb(data, i)
                for _ in range(count):
                    into[addr] = symbol
                    addr += 8 + skip
            else:
                raise ValueError('unknown bind opcode 0x%x' % byte)

    def import_at(self, va: int) -> str | None:
        """The external symbol a slot or stub stands for, if it is one."""
        return (self.stubs.get(va) or self.got.get(va) or self.lazy_pointers.get(va)
                or self.binds.get(va) or self.lazy_binds.get(va))

    # ---- Objective-C ------------------------------------------------------------------------------

    def _pointer_section(self, sectname: str, resolve) -> dict[int, str]:
        sect = self.section(sectname)
        if sect is None:
            return {}
        found = {}
        for k in range(sect.size // 8):
            slot = sect.addr + k * 8
            value = self.u64(slot)
            if value == 0 or not self.mapped(value):
                found[slot] = self.binds.get(slot, '<unbound>')
            else:
                found[slot] = resolve(value)
        return found

    def class_name_at(self, va: int) -> str:
        """The name of the class at ``va``: one of the game's own, by its readable name."""
        cls = getattr(self, 'class_by_address', {}).get(va)
        if cls is not None:
            return cls.name
        for c in getattr(self, '_classes_in_progress', ()):
            if c.address == va:
                return c.name
        return '<class 0x%x>' % va

    def _external_class(self, slot: int) -> str:
        symbol = self.binds.get(slot, '')
        for prefix in ('_OBJC_CLASS_$_', '_OBJC_METACLASS_$_'):
            if symbol.startswith(prefix):
                return symbol[len(prefix):]
        return symbol or '<none>'

    def _method_list(self, va: int, meta: bool) -> list[ObjCMethod]:
        if not va:
            return []
        entsize, count = self.u32(va) & 0xFFFF, self.u32(va + 4)
        methods = []
        for k in range(count):
            e = va + 8 + k * entsize
            methods.append(ObjCMethod(self.cstr(self.u64(e)), self.cstr(self.u64(e + 8)),
                                      self.u64(e + 16), meta))
        return methods

    def _parse_classes(self) -> list[ObjCClass]:
        sect = self.section('__objc_classlist')
        if sect is None:
            return []
        classes = []
        self._classes_in_progress = classes
        for k in range(sect.size // 8):
            cls_va = self.u64(sect.addr + k * 8)
            c = ObjCClass()
            c.address = cls_va
            c.metaclass = self.u64(cls_va)
            ro = self.u64(cls_va + 32)
            c.swift = bool(ro & 3)
            ro &= ~7
            c.flags, _start, c.instance_size = self.u32(ro), self.u32(ro + 4), self.u32(ro + 8)
            c.raw_name = self.cstr(self.u64(ro + 24))
            c.name = demangle_class(c.raw_name)
            c.methods = self._method_list(self.u64(ro + 32), False)
            ivars_va = self.u64(ro + 48)
            if ivars_va:
                entsize, count = self.u32(ivars_va), self.u32(ivars_va + 4)
                for n in range(count):
                    e = ivars_va + 8 + n * entsize
                    off_ptr = self.u64(e)
                    offset = self.u32(off_ptr) if off_ptr else 0
                    name = self.cstr(self.u64(e + 8)) if self.u64(e + 8) else ''
                    typ = self.cstr(self.u64(e + 16)) if self.u64(e + 16) else ''
                    size = self.u32(e + 28)
                    c.ivars.append((offset, name, typ, size))
                    if off_ptr:
                        c.ivar_offset_slots[off_ptr] = name
            props_va = self.u64(ro + 64)
            if props_va:
                entsize, count = self.u32(props_va), self.u32(props_va + 4)
                for n in range(count):
                    e = props_va + 8 + n * entsize
                    c.properties.append((self.cstr(self.u64(e)), self.cstr(self.u64(e + 8))))
            protos_va = self.u64(ro + 40)
            if protos_va:
                for n in range(self.u64(protos_va)):
                    proto = self.u64(protos_va + 8 + n * 8)
                    c.protocols.append(self.cstr(self.u64(proto + 8)))
            # the metaclass's own list holds the class methods
            if c.metaclass and self.mapped(c.metaclass):
                mro = self.u64(c.metaclass + 32) & ~7
                c.methods += self._method_list(self.u64(mro + 32), True)
            super_va = self.u64(cls_va + 8)
            c.superclass = (super_va, cls_va + 8)                # resolved below
            classes.append(c)
        for c in classes:
            super_va, slot = c.superclass
            if super_va and self.mapped(super_va):
                c.superclass = self.class_name_at(super_va)
            else:
                c.superclass = self._external_class(slot)
        del self._classes_in_progress
        return classes

    def methods_by_imp(self) -> dict[int, tuple[ObjCClass, ObjCMethod]]:
        found = {}
        for c in self.classes:
            for m in c.methods:
                found[m.imp] = (c, m)
        return found

    # ---- strings ----------------------------------------------------------------------------------

    def cstrings(self, sectname: str = '__cstring') -> list[tuple[int, str]]:
        """Every NUL-terminated string in a string section, with its address."""
        sect = self.section(sectname)
        if sect is None:
            return []
        blob = self.read(sect.addr, sect.size)
        found, i = [], 0
        while i < len(blob):
            end = blob.find(b'\0', i)
            if end < 0:
                end = len(blob)
            if end > i:
                found.append((sect.addr + i, blob[i:end].decode('utf-8', 'replace')))
            i = end + 1
        return found

    def ustrings(self) -> list[tuple[int, str]]:
        """Every UTF-16 string in __ustring, with its address."""
        sect = self.section('__ustring')
        if sect is None:
            return []
        blob = self.read(sect.addr, sect.size)
        found, i = [], 0
        while i + 1 < len(blob):
            j = i
            while j + 1 < len(blob) and blob[j:j + 2] != b'\0\0':
                j += 2
            if j > i:
                found.append((sect.addr + i, blob[i:j].decode('utf-16-le', 'replace')))
            i = j + 2
        return found

    # ---- Swift 3 reflection -----------------------------------------------------------------------

    def _relative(self, va: int) -> int:
        return va + self.s32(va)

    def swift_fields(self) -> list[tuple[str, list[tuple[str, str]]]]:
        """Each type in __swift3_fieldmd: (mangled type name, [(field name, mangled field type)]).

        Swift 3's descriptor is 12 bytes: a relative pointer to the type's mangled name, a 16-bit kind, a
        16-bit record size and a 32-bit field count (no superclass pointer, which later Swifts added).
        Then come that many records of a 32-bit flags word and relative pointers to the field's mangled
        type and its name.  Read from the bytes on 2026-10-02: RankingCloud's descriptor at 0x10002860c
        is kind 1, record size 12, three fields."""
        sect = self.section('__swift3_fieldmd')
        if sect is None:
            return []
        types = []
        va = sect.addr
        while va + 12 <= sect.end:
            name_va = self._relative(va)
            _kind, record_size, count = self.u16(va + 4), self.u16(va + 6), self.u32(va + 8)
            if record_size < 12 or va + 12 + count * record_size > sect.end:
                raise ValueError('the Swift field descriptor at 0x%x does not read as Swift 3 '
                                 '(record size %d, %d fields)' % (va, record_size, count))
            name = self.cstr(name_va) if self.mapped(name_va) else '?'
            fields = []
            for n in range(count):
                r = va + 12 + n * record_size
                type_va, field_va = self._relative(r + 4), self._relative(r + 8)
                ftype = self.cstr(type_va) if self.s32(r + 4) and self.mapped(type_va) else ''
                fname = self.cstr(field_va) if self.mapped(field_va) else '?'
                fields.append((fname, ftype))
            types.append((name, fields))
            va += 12 + count * record_size
        return types


_shared = None


def load(path: str = None) -> MachO:
    """The binary, parsed once per run."""
    global _shared
    if _shared is None or (path and path != _shared.path):
        _shared = MachO(path)
    return _shared


if __name__ == '__main__':
    m = load()
    print('%s: %d bytes, cryptid %s, entry 0x%x' % (m.path, len(m.data), m.cryptid, m.entry or 0))
    for seg in m.segments:
        print('%-12s 0x%x size 0x%x, file 0x%x' % (seg.name, seg.vmaddr, seg.vmsize, seg.fileoff))
        for sect in seg.sections:
            print('    %-22s 0x%x size 0x%x' % (sect.sectname, sect.addr, sect.size))
    print('%d function starts, %d data-in-code entries, %d stubs, %d got, %d lazy pointers, %d binds'
          % (len(m.function_starts), len(m.data_in_code), len(m.stubs), len(m.got), len(m.lazy_pointers),
             len(m.binds)))
    print('%d classes, %d selector references, %d class references'
          % (len(m.classes), len(m.selrefs), len(m.classrefs)))
    for c in m.classes:
        print('  %s : %s  (%d methods, %d ivars)' % (c.name, c.superclass, len(c.methods), len(c.ivars)))
