import struct
from pathlib import Path
from collections import Counter

def analyze_frequency(path: str):
    p = Path(path)
    data = p.read_bytes()
    
    print(f"--- Analyzing {p.name} ---")
    
    # Count all short integers in range [200, 4800]
    value_counts = Counter()
    
    for i in range(64, len(data) - 2, 2):
        try:
            val = struct.unpack_from("<H", data, i)[0]
            if 200 < val <= 4800:
                value_counts[val] += 1
        except:
            pass
    
    # Categorize by frequency
    unique = [v for v, count in value_counts.items() if count == 1]
    rare = [v for v, count in value_counts.items() if 2 <= count <= 3]
    common = [v for v, count in value_counts.items() if 4 <= count <= 10]
    very_common = [v for v, count in value_counts.items() if count > 10]
    
    print(f"Unique (count=1): {len(unique)} values")
    print(f"Rare (count=2-3): {len(rare)} values")
    print(f"Common (count=4-10): {len(common)} values")
    print(f"Very Common (count>10): {len(very_common)} values")
    
    # Show very common values (likely structural)
    print(f"\nVery common values (likely structural, DON'T scale):")
    for val in sorted(very_common)[:20]:
        print(f"  {val}: appears {value_counts[val]} times")
    
    # Show some unique values (likely timestamps, SAFE to scale)
    print(f"\nSample unique values (likely timestamps, safe to scale):")
    for val in sorted(unique)[:20]:
        print(f"  {val}")
    
    return value_counts

def main():
    f = r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbonebreak\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani"
    analyze_frequency(f)

if __name__ == "__main__":
    main()
