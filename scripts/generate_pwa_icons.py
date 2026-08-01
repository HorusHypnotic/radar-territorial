"""Gera ícones PNG determinísticos do monograma vetorial OPERA."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def png(size: int) -> bytes:
    rows = []
    center = size / 2
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            distance = ((x - center) ** 2 + (y - center) ** 2) ** .5
            bg = (6, 16, 28, 255) if distance < size * .44 else (9, 25, 43, 255)
            line = abs(x - center) < size * .018 or abs((y - center) - .58 * (x - center)) < size * .018 or abs((y - center) + .58 * (x - center)) < size * .018
            color = (40, 165, 255, 255) if line and distance < size * .27 else bg
            row.extend(color)
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def main() -> int:
    target = ROOT / "frontend" / "icons"; target.mkdir(parents=True, exist_ok=True)
    for size in (192, 512): (target / f"icon-{size}.png").write_bytes(png(size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
