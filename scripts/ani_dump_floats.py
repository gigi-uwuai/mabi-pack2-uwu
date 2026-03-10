import struct
from pathlib import Path
import sys

def dump_floats(path: str):
    p = Path(path)
    data = p.read_bytes()
    
    print(f"--- Analyzing {p.name} ---")
    print(f"Total size: {len(data)} bytes")
    
    # Iterate over the file in 4-byte chunks
    found_floats = []
    for i in range(0, len(data) - 4, 4):
        chunk = data[i:i+4]
        try:
            val = struct.unpack("<f", chunk)[0]
            # Filter for plausible timestamp/value ranges
            # Timestamps usually start at 0 and go up to maybe 10-20 seconds for short animations
            # They are usually positive.
            if -100.0 < val < 100.0 and abs(val) > 1e-6: 
                found_floats.append((i, val))
            elif val == 0.0:
                 found_floats.append((i, val))
        except:
            pass

    # Print first 200 floats to see the start of the data
    print("\nFirst 200 Floats found:")
    for i, (offset, val) in enumerate(found_floats[:200]):
        print(f"Offset {offset:04X} ({offset}): {val:.6f}")

    # Look for ANY increasing sequence of floats, even if not contiguous
    # This is a bit looser but might catch things like:
    # [Time1] [Val1] [Val2] [Time2] [Val3] [Val4] ...
    
    print("\n--- Searching for ANY increasing float sequences ---")
    
    # Collect all valid positive floats
    valid_floats = []
    for i in range(0, len(data) - 4, 4):
        chunk = data[i:i+4]
        try:
            val = struct.unpack("<f", chunk)[0]
            if 0.0 <= val < 30.0: # Timestamps usually 0-30s
                valid_floats.append((i, val))
        except:
            pass

    # Just print all valid floats to see if we can spot a pattern manually
    print("\n--- All Valid Positive Floats (0.0 - 30.0) ---")
    for i, (offset, val) in enumerate(valid_floats):
        print(f"{offset:04X}: {val:.6f}")




def main():
    f = r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbreakbone\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani"
    dump_floats(f)

if __name__ == "__main__":
    main()
