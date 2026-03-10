import struct
from pathlib import Path
import sys

def bruteforce_scale(path: str, scale_factor: float = 0.5):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}")
        return

    data = bytearray(p.read_bytes())
    original_len = len(data)
    
    modified_count = 0
    
    # Iterate 4-byte aligned
    for i in range(0, len(data) - 4, 4):
        chunk = data[i:i+4]
        try:
            val = struct.unpack("<f", chunk)[0]
            
            # Criteria for "plausible timestamp"
            # 1. Positive
            # 2. Not too huge (animations are usually < 100s)
            # 3. Not exactly 1.0 (likely scale) or 0.0 (start/default)
            # 4. Not extremely small (noise/epsilon)
            
            if 0.001 < val < 100.0 and abs(val - 1.0) > 0.001:
                new_val = val * scale_factor
                struct.pack_into("<f", data, i, new_val)
                modified_count += 1
        except:
            pass

    out_name = p.with_name(p.stem + "_bruteforce_2x" + p.suffix)
    out_name.write_bytes(data)
    
    print(f"Processed {p.name}")
    print(f"  Modified {modified_count} floats")
    print(f"  Saved to {out_name}")

def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbreakbone\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbreakbone\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        bruteforce_scale(f)

if __name__ == "__main__":
    main()
