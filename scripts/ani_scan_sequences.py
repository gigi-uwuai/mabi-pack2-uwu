import struct
from pathlib import Path
import sys

def scan_sequences(path: str):
    p = Path(path)
    data = p.read_bytes()
    
    print(f"--- Scanning {p.name} ---")
    
    # We are looking for sequences of short integers (2 bytes)
    # where v[i+1] > v[i]
    
    sequences = []
    current_seq = []
    
    print("Scanning for FLOAT sequences (0.0 - 160.0)...")
    
    for stride in [4, 8, 12, 16, 20]:
        found_count = 0
        for start_offset in range(64, 64 + stride, 4):
            current_seq = []
            for i in range(start_offset, len(data) - 4, stride):
                try:
                    val = struct.unpack_from("<f", data, i)[0]
                    
                    if not current_seq:
                        if 0.0 <= val < 160.0:
                            current_seq.append((i, val))
                    else:
                        last_offset, last_val = current_seq[-1]
                        # Check if increasing
                        if val > last_val and (val - last_val) < 1.0 and val <= 160.0:
                            current_seq.append((i, val))
                        else:
                            if len(current_seq) >= 5 and (current_seq[-1][1] - current_seq[0][1]) > 0.1:
                                found_count += 1
                                if found_count <= 5: # Print first 5 found
                                    print(f"Stride {stride}: Found seq len {len(current_seq)} at {hex(current_seq[0][0])}")
                                    print(f"  Values: {current_seq[0][1]:.4f} ... {current_seq[-1][1]:.4f}")
                            current_seq = []
                            if 0.0 <= val < 160.0:
                                current_seq.append((i, val))
                except:
                    pass
        if found_count > 0:
            print(f"Stride {stride}: Found {found_count} sequences.")


def main():
    f = r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani"
    scan_sequences(f)

if __name__ == "__main__":
    main()
