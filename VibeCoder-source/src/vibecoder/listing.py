"""One exact function listing from a Windows PE file.

Capstone decodes the bytes. Nothing here guesses an instruction or runs the file.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

_MAX_FILE = 64 * 1024 * 1024
_MAX_INSNS = 48
_MAX_BYTES = 4096
_EXECUTE = 0x20000000
_MACHINES = {0x14C: ("x86", 32), 0x8664: ("x86-64", 64)}


class ListingError(Exception):
    pass


@dataclass(frozen=True)
class Instruction:
    address: int
    bytes_hex: str
    mnemonic: str
    op: str


@dataclass(frozen=True)
class FunctionListing:
    name: str
    machine: str
    entry: int
    instructions: tuple[Instruction, ...]
    stopped: str


def format_listing(path: str) -> str:
    """Read a PE file and return the entry function as text."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ListingError("That program is not there anymore.")
    try:
        data = file_path.read_bytes()
    except OSError as exc:
        raise ListingError(f"Could not read that program: {exc}") from exc
    if len(data) > _MAX_FILE:
        raise ListingError("That file is too large to list.")
    listing = list_entry(data, file_path.name)
    return render(listing)


def list_entry(data: bytes, name: str) -> FunctionListing:
    machine, bits, image_base, entry_rva, code, code_va = _pe_entry(data)
    instructions, stopped = _disassemble(code, code_va, bits)
    if not instructions:
        raise ListingError("No instructions were decoded at the entry point.")
    return FunctionListing(name, machine, image_base + entry_rva, tuple(instructions), stopped)


def render(listing: FunctionListing) -> str:
    lines = [
        f"; {listing.name}",
        f"; {listing.machine}  entry 0x{listing.entry:x}",
        "; one function, decoded from the entry point",
    ]
    for item in listing.instructions:
        op = f" {item.op}" if item.op else ""
        lines.append(f"0x{item.address:x}  {item.bytes_hex:<24} {item.mnemonic}{op}")
    if listing.stopped:
        lines.append(f"; {listing.stopped}")
    return "\n".join(lines) + "\n"


def _pe_entry(data: bytes) -> tuple[str, int, int, int, bytes, int]:
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ListingError("That file is not a Windows program (PE).")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if e_lfanew <= 0 or e_lfanew + 24 > len(data) or data[e_lfanew : e_lfanew + 4] != b"PE\0\0":
        raise ListingError("That file is not a Windows program (PE).")
    # COFF: Machine, NumberOfSections, then 12 bytes, then SizeOfOptionalHeader.
    machine_id, section_count = struct.unpack_from("<HH", data, e_lfanew + 4)
    optional_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    machine = _MACHINES.get(machine_id)
    if machine is None:
        raise ListingError("This program is not x86. Only x86 and x86-64 can be listed.")
    name, bits = machine
    optional = e_lfanew + 24
    if optional + optional_size > len(data) or optional_size < 32:
        raise ListingError("That program header is incomplete.")
    magic = struct.unpack_from("<H", data, optional)[0]
    entry_rva = struct.unpack_from("<I", data, optional + 16)[0]
    if magic == 0x20B:
        image_base = struct.unpack_from("<Q", data, optional + 24)[0]
    elif magic == 0x10B:
        image_base = struct.unpack_from("<I", data, optional + 28)[0]
    else:
        raise ListingError("That program header is not a known PE optional header.")
    table = optional + optional_size
    chosen: tuple[int, int, int, int] | None = None
    first_exec: tuple[int, int, int, int] | None = None
    for index in range(section_count):
        start = table + index * 40
        if start + 40 > len(data):
            raise ListingError("That program's section table is incomplete.")
        virtual_size, virtual_address, raw_size, raw_ptr = struct.unpack_from("<IIII", data, start + 8)
        flags = struct.unpack_from("<I", data, start + 36)[0]
        if flags & _EXECUTE == 0:
            continue
        span = max(virtual_size, raw_size)
        record = (virtual_address, span, raw_ptr, raw_size)
        if first_exec is None:
            first_exec = record
        if virtual_address <= entry_rva < virtual_address + max(span, 1):
            chosen = record
            break
    if chosen is None:
        chosen = first_exec
    if chosen is None:
        raise ListingError("That program has no executable section.")
    virtual_address, _span, raw_ptr, raw_size = chosen
    if entry_rva < virtual_address:
        offset = 0
        code_rva = virtual_address
    else:
        offset = entry_rva - virtual_address
        code_rva = entry_rva
    file_off = raw_ptr + offset
    if raw_size < offset or file_off > len(data):
        raise ListingError("The entry point is outside the file.")
    available = min(raw_size - offset, len(data) - file_off, _MAX_BYTES)
    if available <= 0:
        raise ListingError("The entry point has no bytes to decode.")
    return name, bits, image_base, code_rva, data[file_off : file_off + available], image_base + code_rva


def _disassemble(code: bytes, address: int, bits: int) -> tuple[list[Instruction], str]:
    try:
        from capstone import CS_ARCH_X86, CS_MODE_32, CS_MODE_64, Cs
    except ImportError as exc:
        raise ListingError(
            "The disassembler is not installed. From VibeCoder-source run: "
            ".venv\\Scripts\\python.exe -m pip install capstone"
        ) from exc
    mode = CS_MODE_64 if bits == 64 else CS_MODE_32
    decoder = Cs(CS_ARCH_X86, mode)
    decoder.skipdata = False
    found: list[Instruction] = []
    stopped = ""
    for item in decoder.disasm(code, address):
        found.append(
            Instruction(
                item.address,
                " ".join(f"{byte:02x}" for byte in item.bytes),
                item.mnemonic,
                item.op_str,
            )
        )
        if item.mnemonic in {"ret", "retf"}:
            stopped = "Stopped at the return."
            break
        if len(found) >= _MAX_INSNS:
            stopped = f"Stopped after {_MAX_INSNS} instructions."
            break
    return found, stopped
