import re

dunbarton_path = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zdunbyzoom\data\world\Uladh_Dunbarton\Uladh_Dunbarton.rgn"
mrd_path = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbrizoom\data\world\MRD_1S\MRD_1S.rgn"

def extract_xml(path):
    with open(path, "rb") as f:
        # Get file size
        f.seek(0, 2)
        size = f.tell()
        # Read last 2000 bytes or whole file if smaller
        seek_amount = min(2000, size)
        f.seek(-seek_amount, 2)
        data = f.read()
    text = data.decode("utf-16le", errors="ignore")
    xml_start = text.find("<region")
    if xml_start != -1:
        return text[xml_start:]
    return "XML not found"

dun_xml = extract_xml(dunbarton_path)
mrd_xml = extract_xml(mrd_path)

print("="*70)
print("DUNBARTON XML:")
print("="*70)
print(dun_xml)
print("\n" + "="*70)
print("MRD_1S XML (WORKING MOD):")
print("="*70)
print(mrd_xml)
print("\n" + "="*70)
print("KEY DIFFERENCES:")
print("="*70)

# Parse key values
def get_value(xml, key):
    match = re.search(rf'{key}="([^"]+)"', xml)
    return match.group(1) if match else "NOT FOUND"

keys = ['farplane_n', 'farplane_f', 'fov', 'zoom_min', 'zoom_max']
print(f"{'Parameter':<20} {'Dunbarton':<20} {'MRD_1S':<20} {'Match'}")
print("-"*70)
for key in keys:
    dun_val = get_value(dun_xml, key)
    mrd_val = get_value(mrd_xml, key)
    match = "✓" if dun_val == mrd_val else "✗ MISMATCH"
    print(f"{key:<20} {dun_val:<20} {mrd_val:<20} {match}")
