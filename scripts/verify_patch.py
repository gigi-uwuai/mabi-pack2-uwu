import re

file_path = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zdunbyzoom\data\world\Uladh_Dunbarton\Uladh_Dunbarton.rgn"

with open(file_path, "rb") as f:
    f.seek(-1000, 2)  # Read last 1000 bytes
    data = f.read()

text = data.decode("utf-16le", errors="ignore")

# Find zoom_max value
zoom_match = re.search(r'zoom_max="([\d\.]+)"', text)
if zoom_match:
    print(f"✓ Found zoom_max: {zoom_match.group(1)}")
else:
    print("✗ zoom_max not found in file!")

# Show the full XML section
xml_start = text.find("<region")
if xml_start != -1:
    print("\nFull Dunbarton XML:")
    print(text[xml_start:])
else:
    print("\n✗ No <region> tag found")

# Now compare with MRD_1S
print("\n" + "="*60)
print("Comparing with working MRD_1S.rgn:")
print("="*60)

mrd_path = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbrizoom\data\world\MRD_1S\MRD_1S.rgn"
try:
    with open(mrd_path, "rb") as f:
        f.seek(-500, 2)
        mrd_tail = f.read()
    mrd_text = mrd_tail.decode("utf-16le", errors="ignore")
    mrd_xml_start = mrd_text.find("<region")
    if mrd_xml_start != -1:
        print("\nMRD_1S XML:")
        print(mrd_text[mrd_xml_start:])
except Exception as e:
    print(f"Could not read MRD: {e}")
