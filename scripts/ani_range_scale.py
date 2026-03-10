import struct
from pathlib import Path
import sys

def range_scale(path: str, scale_factor: float = 0.5):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}")
        return

    data = bytearray(p.read_bytes())
    
    print(f"--- Processing {p.name} ---")
    
    # 1. Update Header
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

    # 2. Scale Shorts in Range [200, 4800]
    
    modified_count = 0
    header_size = 64
    limit_val = orig_ticks # 4800
    min_val = 200
    
    # Iterate 2-byte aligned, skipping header
    for i in range(header_size, len(data) - 2, 2):
        try:
            val = struct.unpack_from("<H", data, i)[0]
            
            if min_val < val <= limit_val:
                new_val = int(val * scale_factor)
                struct.pack_into("<H", data, i, new_val)
                modified_count += 1
        except:
            pass

    out_name = p.with_name(p.stem + "_range_scale" + p.suffix)
    out_name.write_bytes(data)
    
    print(f"  Modified {modified_count} short integers (Range {min_val}-{limit_val})")
    print(f"  Saved to {out_name}")

def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        range_scale(f)

if __name__ == "__main__":
    main()
