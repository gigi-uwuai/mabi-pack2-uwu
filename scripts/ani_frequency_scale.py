import struct
from pathlib import Path
from collections import Counter

def frequency_scale(path: str, scale_factor: float = 0.5):
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

    # 2. Analyze frequency
    value_counts = Counter()
    value_locations = {}  # Track where each value appears
    
    header_size = 64
    for i in range(header_size, len(data) - 2, 2):
        try:
            val = struct.unpack_from("<H", data, i)[0]
            if 200 < val <= orig_ticks:
                value_counts[val] += 1
                if val not in value_locations:
                    value_locations[val] = []
                value_locations[val].append(i)
        except:
            pass
    
    # 3. Scale ONLY unique values (count <= 3)
    # We allow up to 3 to catch some values that might appear in multiple tracks
    # but are still likely timestamps
    
    modified_count = 0
    max_frequency = 3
    
    for val, count in value_counts.items():
        if count <= max_frequency:
            new_val = int(val * scale_factor)
            # Replace all occurrences of this value
            for offset in value_locations[val]:
                struct.pack_into("<H", data, offset, new_val)
                modified_count += 1
    
    unique_values = len([v for v, c in value_counts.items() if c <= max_frequency])
    
    out_name = p.with_name(p.stem + "_freq_scale" + p.suffix)
    out_name.write_bytes(data)
    
    print(f"  Scaled {unique_values} unique values ({modified_count} total modifications)")
    print(f"  Left untouched: {len(value_counts) - unique_values} repeated values")
    print(f"  Saved to {out_name}")

def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        frequency_scale(f)

if __name__ == "__main__":
    main()
