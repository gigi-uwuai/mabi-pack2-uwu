import struct
from pathlib import Path
import sys

def scale_shorts(path: str, scale_factor: float = 0.5):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}")
        return

    data = bytearray(p.read_bytes())
    
    print(f"--- Processing {p.name} ---")
    
    # 1. Update Header
    # 0x0C: Total Frames (Short)
    # 0x0E: Total Ticks (Short)
    
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
        
        limit_val = orig_ticks # We only scale values <= original total ticks
    except Exception as e:
        print(f"Error updating header: {e}")
        return

    # 2. Scan and Scale Data
    # We look for any short integer (2 bytes) that is <= limit_val and > 10 (to avoid indices)
    
    modified_count = 0
    header_size = 64
    
    # Iterate 2-byte aligned, skipping header
    for i in range(header_size, len(data) - 2, 2):
        try:
            val = struct.unpack_from("<H", data, i)[0]
            
            # Criteria:
            # - Must be positive
            # - Must be <= original max ticks (e.g. 4800)
            # - Must be > 10 (heuristic to avoid bone indices, counts, etc which are usually small)
            # - Must NOT be 0 (0 is usually start time, scaling 0 is 0, but we don't want to touch it if it's an index)
            # Actually, 0 timestamp is valid. But 0 index is also valid. 
            # Let's be safe and only scale > 10 for now. If it starts slow, we know why.
            
            if 10 < val <= limit_val:
                new_val = int(val * scale_factor)
                struct.pack_into("<H", data, i, new_val)
                modified_count += 1
        except:
            pass

    out_name = p.with_name(p.stem + "_short_scale" + p.suffix)
    out_name.write_bytes(data)
    
    print(f"  Modified {modified_count} short integers")
    print(f"  Saved to {out_name}")

def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        scale_shorts(f)

if __name__ == "__main__":
    main()
