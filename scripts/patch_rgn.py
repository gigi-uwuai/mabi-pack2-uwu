import os

file_path = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zdunbyzoom\data\world\Uladh_Dunbarton\Uladh_Dunbarton.rgn"

with open(file_path, "rb") as f:
    data = f.read()

# Target: zoom_max="1500.000000" (11 chars for the number)
# Replacement: zoom_max="25000.00000" (11 chars for the number, removing one decimal place to match length)

# The file uses UTF-16LE encoding for the XML part at the end
search_pattern = 'zoom_max="1500.000000"'.encode("utf-16le")
replacement = 'zoom_max="25000.00000"'.encode("utf-16le")

if search_pattern in data:
    new_data = data.replace(search_pattern, replacement)
    with open(file_path, "wb") as f:
        f.write(new_data)
    print(f"Successfully patched {file_path}")
else:
    print(f"Pattern not found in {file_path}")
