import struct
from pathlib import Path
import sys

def surgical_scale(path: str, scale_factor: float = 0.5):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}")
        return

    data = bytearray(p.read_bytes())
    
    print(f"--- Processing {p.name} ---")
    
    # 1. Read and Update Header
    try:
        orig_frames = struct.unpack_from("<H", data, 12)[0]
        orig_ticks = struct.unpack_from("<H", data, 14)[0]
        
        new_frames = int(orig_frames * scale_factor)
        new_ticks = int(orig_ticks * scale_factor)
        
        struct.pack_into("<H", data, 12, new_frames)
        struct.pack_into("<H", data, 14, new_ticks)
        
        print(f"Header Updated:")
        print(f"  Frames: {orig_frames} -> {new_frames}")
        print(f"  Ticks:  {orig_ticks} -> {new_ticks}")
        
    except Exception as e:
        print(f"Error updating header: {e}")
        return

    # 2. Find and Replace Duration Values
    # We look for the exact short integer 'orig_ticks' and replace it with 'new_ticks'
    
    modified_count = 0
    header_size = 64
    
    # Iterate 2-byte aligned, skipping header
    for i in range(header_size, len(data) - 2, 2):
        try:
            val = struct.unpack_from("<H", data, i)[0]
            
            if val == orig_ticks:
                struct.pack_into("<H", data, i, new_ticks)
                modified_count += 1
        except:
            pass

    out_name = p.with_name(p.stem + "_surgical" + p.suffix)
    out_name.write_bytes(data)
    
    print(f"  Replaced {modified_count} occurrences of {orig_ticks}")
    print(f"  Saved to {out_name}")

def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        surgical_scale(f)

if __name__ == "__main__":
    main()
