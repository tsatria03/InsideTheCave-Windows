"""Disassemble Inside The Cave's arm64 code, annotated.

Capstone does the decoding; this follows the registers well enough to say what each address the code
builds or loads is:

* ``adr``, and ``adrp`` with the ``add`` or ``ldr`` after it, resolved to a string, a selector, a class,
  an import, a function, a field offset, or a number in a constant pool
* ``bl`` and ``b`` to a stub named by its import (``objc_msgSend``, ``swift_retain``), and to one of the
  game's own functions by the name tools/names.py gives it
* ``objc_msgSend`` with the selector it is sent
* a stored property of the function's own class, read or written through its field-offset global
  (Swift reaches the stored properties of a class with an Objective-C ancestor that way)
* ``ldr`` of a float or a double from a constant pool, with its value

The register following is linear and forgets everything at a branch target and after a call, so an
annotation is what the bytes say on the straight path into that instruction.  It is a reading aid; the
instructions themselves are always printed in full.

    python tools/dz.py 0x1000157d0 0x100015800          an address range
    python tools/dz.py 0x100015620                      the whole function that starts there
    python tools/dz.py "-[GameScene createMonster]"     a function by its name
"""
from __future__ import annotations

import bisect
import struct
import sys

import capstone
from capstone import arm64 as A

import macho

#: The registers a call may change: x0 to x18, and the flags.  Their values are forgotten after a bl.
CALL_CLOBBERED = {'x%d' % n for n in range(19)} | {'x30'}


def number(value: int) -> str:
    """A 64-bit constant as the code may mean it: the integer, and the double its bits make when that
    is a plain number (so 0xbfd3333333333333 reads as -0.3)."""
    text = '%d' % value if value < 1 << 20 else '0x%x' % value
    if value >> 48:
        d = struct.unpack('<d', struct.pack('<Q', value))[0]
        if d == d and abs(d) < 1e9 and (d == 0 or abs(d) > 1e-6):
            text += ' (double %r)' % d
    return text


def class_short(name: str) -> str:
    """'_OBJC_CLASS_$_SKSpriteNode' -> 'SKSpriteNode'."""
    for prefix in ('_OBJC_CLASS_$_', '_OBJC_METACLASS_$_'):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def norm(reg: str) -> str:
    """'w5' -> 'x5', so a write to either half forgets the register."""
    if reg and reg[0] == 'w' and reg[1:].isdigit():
        return 'x' + reg[1:]
    return reg


class Insn:
    """One instruction, or one word capstone could not decode, with what is known about it."""
    __slots__ = ('address', 'mnemonic', 'op_str', 'size', 'notes', 'target', 'kind', 'ref')

    def __init__(self, address, mnemonic, op_str, size=4):
        self.address, self.mnemonic, self.op_str, self.size = address, mnemonic, op_str, size
        self.notes: list[str] = []
        self.target = None          # a branch or call target
        self.kind = ''              # 'call', 'jump', 'cond', 'ret', 'word'
        self.ref = None             # an address in the code this instruction takes, such as a closure's

    def text(self) -> str:
        line = '  0x%x  %-7s %s' % (self.address, self.mnemonic, self.op_str)
        if self.notes:
            line = '%-60s ; %s' % (line, '; '.join(self.notes))
        return line


class Disassembler:
    def __init__(self, m: macho.MachO = None, names: dict = None):
        self.m = m or macho.load()
        self.md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
        self.md.detail = True
        text = self.m.section('__text')
        self.text = text
        self.starts = sorted(s for s in self.m.function_starts if s in text)
        self.names = names or {}                                     # address -> function name
        self.imps = self.m.methods_by_imp()
        self.ivar_slots = {}
        for c in self.m.classes:
            for slot, ivar in c.ivar_offset_slots.items():
                self.ivar_slots[slot] = '%s.%s' % (c.name, ivar)
        self.class_metadata = {c.address: c.name for c in self.m.classes}
        self.class_metadata.update({c.metaclass: c.name + ' (metaclass)' for c in self.m.classes})
        self.strings = dict(self.m.cstrings())
        self.methnames = dict(self.m.cstrings('__objc_methname'))
        self.ustrings = dict(self.m.ustrings())
        self.typerefs = dict(self.m.cstrings('__swift3_typeref'))

    # ---- functions --------------------------------------------------------------------------------

    def bounds(self, start: int) -> tuple[int, int]:
        """The function that ``start`` is in: (its start, the next function's start)."""
        i = bisect.bisect_right(self.starts, start) - 1
        begin = self.starts[i] if i >= 0 else self.text.addr
        end = self.starts[i + 1] if i + 1 < len(self.starts) else self.text.end
        return begin, end

    def name_of(self, va: int) -> str:
        if va in self.names:
            return self.names[va]
        if va in self.imps:
            c, meth = self.imps[va]
            return meth.name(c.name)
        return 'fn_%x' % va

    # ---- decoding ---------------------------------------------------------------------------------

    def decode(self, start: int, end: int) -> list:
        """Every 4-byte word from start to end: capstone's instruction, or ``.word`` where it cannot
        decode one, so nothing between the two addresses is ever skipped."""
        code = self.m.read(start, end - start)
        out = []
        pos = 0
        while pos < len(code):
            got = False
            for ins in self.md.disasm(code[pos:], start + pos):
                out.append(ins)
                pos += ins.size
                got = True
            if pos < len(code):
                if not got or True:
                    word = struct.unpack_from('<I', code, pos)[0]
                    out.append(('.word', start + pos, word))
                    pos += 4
        return out

    # ---- what an address is -----------------------------------------------------------------------

    def describe(self, va: int, loaded: bool = False, width: int = 8, reg: str = '') -> str | None:
        """What lives at ``va``, in words; ``loaded`` means the code reads from it rather than taking
        its address."""
        m = self.m
        if va in self.ivar_slots:
            return 'offset of ' + self.ivar_slots[va]
        if va in m.selrefs:
            return '@selector(%s)' % m.selrefs[va]
        if va in m.classrefs:
            return 'class ' + class_short(m.classrefs[va])
        if va in m.superrefs:
            return 'super ' + class_short(m.superrefs[va])
        imp = m.import_at(va)
        if imp:
            return ('import ' if loaded else '&import ') + imp
        if va in self.strings:
            return repr(self.strings[va])
        if va in self.methnames:
            return 'selector name %r' % self.methnames[va]
        if va in self.ustrings:
            return 'u' + repr(self.ustrings[va])
        if va in self.typerefs:
            return 'typeref %r' % self.typerefs[va]
        if va in self.class_metadata:
            return 'class metadata ' + self.class_metadata[va]
        if self.text.addr <= va < self.text.end:
            begin, _ = self.bounds(va)
            name = self.name_of(begin)
            return ('&' + name) if begin == va else '&%s+0x%x' % (name, va - begin)
        sect = m.section_of(va)
        if sect is None:
            return None
        where = '%s,%s' % (sect.segname, sect.sectname)
        if loaded and sect.sectname not in ('__bss', '__common'):
            try:
                if reg.startswith('d'):
                    return '%s double %r' % (where, m.f64(va))
                if reg.startswith('s'):
                    return '%s float %r' % (where, m.f32(va))
                if reg.startswith('q'):
                    a, b = m.f64(va), m.f64(va + 8)
                    return '%s doubles (%r, %r)' % (where, a, b)
                if reg.startswith('x'):
                    value = m.u64(va)
                    inner = self.describe(value) if value and m.mapped(value) else None
                    return '%s 0x%x%s' % (where, value, ' -> ' + inner if inner else '')
            except (ValueError, struct.error):
                pass
        return '%s 0x%x' % (where, va)

    # ---- annotating a function ---------------------------------------------------------------------

    def function(self, start: int) -> list[Insn]:
        begin, end = self.bounds(start)
        raw = self.decode(begin, end)
        targets = set()
        for ins in raw:
            if isinstance(ins, tuple):
                continue
            for op in ins.operands:
                if op.type == A.ARM64_OP_IMM and ins.group(capstone.CS_GRP_JUMP) and begin <= op.imm < end:
                    targets.add(op.imm)
        state: dict[str, tuple] = {}
        self_reg = self._self_register(begin)
        if self_reg:
            state[self_reg] = ('self',)
        out = []
        for ins in raw:
            if isinstance(ins, tuple):
                _, va, word = ins
                x = Insn(va, '.word', '0x%08x' % word)
                x.kind = 'word'
                x.notes.append('capstone cannot decode this word')
                out.append(x)
                state.clear()
                continue
            if ins.address in targets:
                state = {}
            x = Insn(ins.address, ins.mnemonic, ins.op_str, ins.size)
            self._step(ins, x, state)
            out.append(x)
        return out

    def _self_register(self, begin: int) -> str | None:
        """Where ``self`` arrives: x0 in an Objective-C method, x20 (swiftself) in a Swift method body
        named through its thunk."""
        if begin in self.imps:
            return 'x0'
        name = self.names.get(begin, '')
        if name and '.' in name and '~' not in name and not name.startswith(('-[', '+[')):
            return 'x20'
        return None

    def _owner_class(self, va: int) -> str | None:
        name = self.name_of(self.bounds(va)[0])
        if name.startswith(('-[', '+[')):
            return name[2:].split(' ')[0]
        head = name.split('~')[0].split('.')[0]
        return head if any(c.name == head for c in self.m.classes) else None

    def _step(self, ins, x: Insn, state: dict):
        mn = ins.mnemonic
        ops = ins.operands
        regname = ins.reg_name

        def reg(op):
            return norm(regname(op.reg))

        def val(r):
            return state.get(r)

        if mn in ('mov', 'movz', 'movn') and len(ops) == 2 and ops[1].type == A.ARM64_OP_IMM:
            value = ops[1].imm & 0xFFFFFFFFFFFFFFFF
            if regname(ops[0].reg).startswith('w'):
                value &= 0xFFFFFFFF
            state[reg(ops[0])] = ('imm', value)
            return
        if mn == 'movk' and ops[1].type == A.ARM64_OP_IMM:
            r = reg(ops[0])
            prior = val(r)
            shift = ops[1].shift.value if ops[1].shift.type == A.ARM64_SFT_LSL else 0
            if prior and prior[0] == 'imm':
                value = (prior[1] & ~(0xFFFF << shift)) | ((ops[1].imm & 0xFFFF) << shift)
                state[r] = ('imm', value)
                x.notes.append(number(value))
            else:
                state.pop(r, None)
            return
        if mn == 'adrp' or mn == 'adr':
            r = reg(ops[0])
            state[r] = ('addr', ops[1].imm)
            if mn == 'adr':
                d = self.describe(ops[1].imm)
                if d:
                    x.notes.append(d)
                if self.text.addr <= ops[1].imm < self.text.end:
                    x.ref = ops[1].imm
            return
        if mn == 'add' and len(ops) == 3 and ops[2].type == A.ARM64_OP_IMM:
            src = val(reg(ops[1]))
            dst = reg(ops[0])
            imm = ops[2].imm << (ops[2].shift.value if ops[2].shift.type == A.ARM64_SFT_LSL else 0)
            if src and src[0] == 'addr':
                va = src[1] + imm
                state[dst] = ('addr', va)
                d = self.describe(va)
                if d:
                    x.notes.append(d)
                if self.text.addr <= va < self.text.end:
                    x.ref = va
            else:
                state.pop(dst, None)
            return
        if mn == 'add' and len(ops) == 3 and ops[2].type == A.ARM64_OP_REG:
            a, b = val(reg(ops[1])), val(reg(ops[2]))
            dst = reg(ops[0])
            field = next((v[1] for v in (a, b) if v and v[0] == 'field'), None)
            if field:
                state[dst] = ('fieldaddr', field)
                x.notes.append('&' + field)
            else:
                state.pop(dst, None)
            return
        if mn == 'mov' and len(ops) == 2 and ops[1].type == A.ARM64_OP_REG:
            src = val(reg(ops[1]))
            dst = reg(ops[0])
            if src:
                state[dst] = src
            else:
                state.pop(dst, None)
            return
        if ins.group(capstone.CS_GRP_CALL) or ins.group(capstone.CS_GRP_JUMP) or mn in ('ret', 'br', 'blr'):
            self._branch(ins, x, state)
            return
        # loads and stores through memory
        mem = next((op for op in ops if op.type == A.ARM64_OP_MEM), None)
        if mem is not None:
            base = norm(regname(mem.mem.base)) if mem.mem.base else ''
            index = norm(regname(mem.mem.index)) if mem.mem.index else ''
            b, i = val(base), val(index) if index else None
            note = None
            loaded_reg = regname(ops[0].reg) if ops[0].type == A.ARM64_OP_REG else ''
            is_load = mn.startswith('ld')
            if b and b[0] == 'addr' and not index:
                va = b[1] + mem.mem.disp
                note = self.describe(va, loaded=is_load, reg=loaded_reg)
                if is_load and ops[0].type == A.ARM64_OP_REG:
                    self._loaded(norm(regname(ops[0].reg)), va, state)
                    if mn == 'ldp' and len(ops) > 2:
                        state.pop(norm(regname(ops[1].reg)), None)
                    if note:
                        x.notes.append(note)
                    return
            elif i and i[0] == 'field':
                note = ('read ' if is_load else 'write ') + i[1]
            elif b and b[0] == 'fieldaddr' and mem.mem.disp == 0:
                note = ('read ' if is_load else 'write ') + b[1]
            elif b and b[0] == 'self' and mem.mem.disp:
                note = 'self+0x%x' % mem.mem.disp
            if note:
                x.notes.append(note)
            if not is_load and ops[0].type == A.ARM64_OP_REG:
                stored = val(norm(regname(ops[0].reg)))
                if stored and stored[0] == 'imm':
                    x.notes.append('= ' + number(stored[1]))
            if is_load:
                for op in ops:
                    if op.type == A.ARM64_OP_REG:
                        state.pop(norm(regname(op.reg)), None)
            if ins.writeback and base:
                state.pop(base, None)
            return
        if mn.startswith('ldr') and len(ops) == 2 and ops[1].type == A.ARM64_OP_IMM:   # literal
            d = self.describe(ops[1].imm, loaded=True, reg=regname(ops[0].reg))
            if d:
                x.notes.append(d)
            self._loaded(reg(ops[0]), ops[1].imm, state)
            return
        if mn in ('fmov',) and len(ops) == 2 and ops[1].type == A.ARM64_OP_FP:
            return
        # anything else that writes its first operand forgets it
        if ops and ops[0].type == A.ARM64_OP_REG and not mn.startswith(('cmp', 'cmn', 'tst', 'st', 'fcmp',
                                                                         'ccmp', 'nop', 'prfm')):
            state.pop(reg(ops[0]), None)

    def _loaded(self, dst: str, va: int, state: dict):
        """What a register holds after it is loaded from ``va``."""
        m = self.m
        if va in self.ivar_slots:
            state[dst] = ('field', self.ivar_slots[va])
        elif va in m.selrefs:
            state[dst] = ('sel', m.selrefs[va])
        elif va in m.classrefs:
            state[dst] = ('cls', class_short(m.classrefs[va]))
        elif m.import_at(va):
            state[dst] = ('import', m.import_at(va))
        else:
            state.pop(dst, None)

    def _branch(self, ins, x: Insn, state: dict):
        mn = ins.mnemonic
        target = next((op.imm for op in ins.operands if op.type == A.ARM64_OP_IMM), None)
        if mn in ('ret',):
            x.kind = 'ret'
            return
        if mn in ('br', 'blr'):
            x.kind = 'call' if mn == 'blr' else 'jump'
            r = state.get(norm(ins.reg_name(ins.operands[0].reg)))
            if r and r[0] == 'import':
                x.notes.append(r[1])
            if mn == 'blr':
                for k in CALL_CLOBBERED:
                    state.pop(k, None)
            return
        x.target = target
        is_call = mn == 'bl'
        x.kind = 'call' if is_call else ('jump' if mn == 'b' else 'cond')
        result = None
        if target is not None:
            begin, end = self.bounds(x.address)
            imp = self.m.import_at(target)
            if imp:
                note = imp
                if imp.startswith('_objc_msgSend'):
                    sel = state.get('x1')
                    recv = state.get('x0')
                    if sel and sel[0] == 'sel':
                        if recv and recv[0] in ('cls', 'obj'):
                            who = recv[1] if recv[0] == 'cls' else 'a new ' + recv[1]
                        elif recv and recv[0] == 'self':
                            who = 'self'
                        else:
                            who = '?'
                        note += '  [%s %s]' % (who, sel[1])
                        # alloc and init hand back an object of the class they were sent to
                        if recv and recv[0] == 'cls' and sel[1] in ('alloc', 'allocWithZone:', 'new'):
                            result = ('obj', recv[1])
                        elif recv and recv[0] == 'obj' and sel[1].startswith('init'):
                            result = recv
                x.notes.append(note)
            elif not (begin <= target < end) and self.text.addr <= target < self.text.end:
                d = self.describe(target)
                if d:
                    x.notes.append(d[1:] if d.startswith('&') else d)
        if is_call:
            for k in CALL_CLOBBERED:
                state.pop(k, None)
            if result:
                state['x0'] = result


def listing(d: Disassembler, start: int) -> str:
    begin, end = d.bounds(start)
    lines = ['//// %s  0x%x..0x%x' % (d.name_of(begin), begin, end)]
    lines += [x.text() for x in d.function(begin)]
    return '\n'.join(lines)


def main(argv) -> int:
    d = Disassembler()
    try:
        import names
        d.names = names.load_names(d)
    except Exception:          # the names are a help, not a need
        pass
    if not argv:
        print(__doc__)
        return 2
    if argv[0].startswith('0x'):
        start = int(argv[0], 16)
        if len(argv) > 1:
            end = int(argv[1], 16)
            for va in d.starts:
                if start <= va < end:
                    print(listing(d, va))
                    print()
            if not any(start <= va < end for va in d.starts):
                print(listing(d, start))
            return 0
        print(listing(d, start))
        return 0
    wanted = ' '.join(argv)
    hits = [va for va in d.starts if d.name_of(va) == wanted]
    if not hits:
        hits = [va for va in d.starts if wanted in d.name_of(va)]
    for va in hits:
        print(listing(d, va))
        print()
    if not hits:
        print('no function is called %r' % wanted)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
