import struct
from pathlib import Path

def inspect_tracks(path: str):
    p = Path(path)
    data = p.read_bytes()
    
    print(f"--- Inspecting {p.name} ---")
    
    # We know 4800 is the total ticks
    target_val = 4800
    
    found_offsets = []
    for i in range(0, len(data) - 2, 2):
        try:
            val = struct.unpack_from("<H", data, i)[0]
            if val == target_val:
                found_offsets.append(i)
        except:
            pass
            
    print(f"Found {target_val} at {len(found_offsets)} locations.")
    
    for off in found_offsets:
        start = max(0, off - 16)
        end = min(len(data), off + 32) # Look ahead more
        chunk = data[start:end]
        
        print(f"\nOffset {off:04X}:")
        print(f"  Context Hex: {chunk.hex(' ')}")
        
        # Print as shorts
        shorts = []
        for i in range(0, len(chunk), 2):
            current_abs_offset = start + i
            try:
                val = struct.unpack_from('<H', chunk, i)[0]
                if current_abs_offset == off:
                    shorts.append(f"[{val}]")
                else:
                    shorts.append(str(val))
            except:
                pass
        print(f"  Shorts:  {' '.join(shorts)}")

def main():
    f = r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani"
    inspect_tracks(f)

if __name__ == "__main__":
    main()
