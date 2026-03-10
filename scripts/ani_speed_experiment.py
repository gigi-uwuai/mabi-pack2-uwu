import struct
from pathlib import Path
import sys

def modify_ani_speed(path: str):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}")
        return

    data = bytearray(p.read_bytes())
    
    # Read current values
    # Offset 0x0A (10): Likely FPS (uint32 or uint16? usually 4 bytes in these formats, but let's check 2 and 4)
    # The hex dump showed "1E 00 00 00" (if 4 bytes) or "1E 00" (if 2 bytes). 
    # Let's assume 32-bit int for now as it's common aligned.
    
    try:
        current_fps = struct.unpack_from("<H", data, 10)[0]
        print(f"Current Value at 0x0A (FPS?): {current_fps}")
    except Exception as e:
        print(f"Could not read FPS at 0x0A: {e}")
        return

    try:
        current_speed = struct.unpack_from("<f", data, 54)[0]
        print(f"Current Value at 0x36 (Speed?): {current_speed}")
    except Exception as e:
        print(f"Could not read Speed at 0x36: {e}")
        return

    # 1. Create FPS modified version (Double FPS to 60)
    # If 30 is normal speed, telling it it's 60 might make it play faster (if engine tries to match) 
    # OR slower (if engine plays 60 frames per second but we only have 30 frames of data).
    # Usually, increasing FPS value in header makes it play FASTER because it consumes frames faster.
    new_fps = 60
    data_fps = bytearray(data)
    struct.pack_into("<I", data_fps, 10, new_fps)
    
    out_fps = p.with_name(p.stem + "_fps60" + p.suffix)
    out_fps.write_bytes(data_fps)
    print(f"Created: {out_fps} (FPS set to {new_fps})")

    # 2. Create Speed Multiplier modified version (2.0x)
    # If 1.0 is normal, 2.0 might be 2x speed.
    new_speed = 2.0
    data_speed = bytearray(data)
    struct.pack_into("<f", data_speed, 54, new_speed)
    
    out_speed = p.with_name(p.stem + "_speed2x" + p.suffix)
    out_speed.write_bytes(data_speed)
    print(f"Created: {out_speed} (Speed set to {new_speed})")

def main():
    files = [
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbreakbone\data\gfx\char\chapter4\human\anim\tool\Rhand_A\human_tool_rhand_a01_line_break.ani",
        r"E:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbreakbone\data\gfx\char\chapter4\human\anim\tool\Bhand_E\human_tool_rhand_e01_line_break.ani",
    ]

    for f in files:
        print(f"--- Processing {Path(f).name} ---")
        modify_ani_speed(f)
        print()

if __name__ == "__main__":
    main()
