import struct
from pathlib import Path


def speed_up_ani_file(path: str, factor: float) -> None:
    """
    Heuristically speed up a Mabinogi .ani file by scaling any 32-bit
    little-endian floats that look like timing values (0.01..20.0).
    factor < 1.0 => faster playback, factor > 1.0 => slower.

    WARNING: This does not understand the real .ani format. It just assumes
    that many timing values are stored as 32-bit floats within a plausible
    range. Always keep backups and test in-game.
    """
    p = Path(path)

    # Read original bytes
    original_bytes = p.read_bytes()
    data = bytearray(original_bytes)

    # Track how many values we actually changed
    modified_count = 0

    # Scan 4-byte aligned offsets
    for off in range(0, len(data) - 4, 4):
        chunk = data[off:off + 4]
        (val,) = struct.unpack("<f", chunk)

        # Only touch plausible timing-like floats
        if 0.01 <= val <= 20.0:
            new_val = val * factor
            struct.pack_into("<f", data, off, new_val)
            modified_count += 1

    # Backup original once
    backup = p.with_suffix(p.suffix + ".bak")
    if not backup.exists():
        backup.write_bytes(original_bytes)
        print(f"[BACKUP] Created backup: {backup}")
    else:
        print(f"[BACKUP] Existing backup kept: {backup}")

    # Write modified file
    p.write_bytes(data)
    print(f"[OK] {path} - modified {modified_count} float(s)")


def main() -> None:
    # factor < 1.0 means shorter durations -> faster playback.
    factor = 0.7  # 0.7x duration ≈ 30% faster

    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbreakbone\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbreakbone\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        print(f"Processing {f} ...")
        speed_up_ani_file(f, factor)


if __name__ == "__main__":
    main()