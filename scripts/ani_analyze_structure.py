import struct
from pathlib import Path
import sys

def analyze_integers(path: str):
    p = Path(path)
    data = p.read_bytes()
    
    print(f"--- Analyzing {p.name} ---")
    
    # Read Header Values (first 64 bytes)
    try:
        fps = struct.unpack_from("<H", data, 10)[0]
        print(f"Header 0x0A (FPS): {fps}")
        
        total_frames = struct.unpack_from("<H", data, 12)[0]
        print(f"Header 0x0C (Total Frames): {total_frames}")
        
        total_ticks = struct.unpack_from("<H", data, 14)[0]
        print(f"Header 0x0E (Total Ticks?): {total_ticks}")
        
        # Check if Ticks = Frames * FPS
        if fps * total_frames == total_ticks:
            print(f"  -> Confirmed: {total_frames} frames * {fps} fps = {total_ticks} ticks")
    except:
        print("Could not read header values.")

    # Scan for the "Total Ticks" value (e.g. 4800)
    if 'total_ticks' in locals():
        target_val = total_ticks
        print(f"\nSearching for value {target_val} (0x{target_val:X})...")
        
        found_offsets = []
        # Scan 2-byte aligned for shorts
        for i in range(0, len(data) - 2, 2):
            try:
                val = struct.unpack_from("<H", data, i)[0]
                if val == target_val:
                    found_offsets.append(i)
            except:
                pass
                
        print(f"Found {target_val} at offsets: {[hex(x) for x in found_offsets]}")
        
        # Also scan for 4-byte ints just in case
        found_offsets_int = []
        for i in range(0, len(data) - 4, 4):
            try:
                val = struct.unpack_from("<I", data, i)[0]
                if val == target_val:
                    found_offsets_int.append(i)
            except:
                pass
        print(f"Found {target_val} (as int32) at offsets: {[hex(x) for x in found_offsets_int]}")

    # Scan for increasing sequences of shorts (0, 1, 2... or 0, 100, 200...)
    print("\nScanning for increasing SHORT sequences:")
    
    # Try to find a sequence that goes up to total_ticks
    current_seq = []
    for i in range(0, len(data) - 2, 2):
        try:
            val = struct.unpack_from("<H", data, i)[0]
            
            if not current_seq:
                if val == 0:
                    current_seq.append((i, val))
            else:
                last_offset, last_val = current_seq[-1]
                # Check if increasing
                if val > last_val and (val - last_val) < 500: # Allow jumps up to 500 ticks
                    current_seq.append((i, val))
                else:
                    if len(current_seq) > 10 and current_seq[-1][1] > 100:
                        print(f"Found sequence of {len(current_seq)} shorts starting at {hex(current_seq[0][0])}:")
                        print(f"  Range: {current_seq[0][1]} -> {current_seq[-1][1]}")
                    current_seq = []
                    if val == 0:
                        current_seq.append((i, val))
        except:
            pass


def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
    ]

    for f in files:
        analyze_integers(f)

if __name__ == "__main__":
    main()
