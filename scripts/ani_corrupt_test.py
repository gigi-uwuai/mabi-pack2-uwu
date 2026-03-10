import struct
from pathlib import Path
import sys

def corrupt_file(path: str):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}")
        return

    data = bytearray(p.read_bytes())
    
    # Keep header (first 64 bytes) to ensure game recognizes file type
    # Zero out the rest
    header_size = 64
    if len(data) > header_size:
        print(f"Corrupting {p.name} (keeping first {header_size} bytes)...")
        for i in range(header_size, len(data)):
            data[i] = 0
    else:
        print(f"File too small to corrupt safely: {len(data)} bytes")
        return

    out_name = p.with_name(p.stem + "_corrupt" + p.suffix)
    out_name.write_bytes(data)
    
    print(f"Created: {out_name}")
    print("RENAME this file to the original name to test if the game loads it.")

def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        corrupt_file(f)

if __name__ == "__main__":
    main()
