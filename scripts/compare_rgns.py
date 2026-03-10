import os

file_mrd = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zbrizoom\data\world\MRD_1S\MRD_1S.rgn"
file_dun = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zdunbyzoom\data\world\Uladh_Dunbarton\Uladh_Dunbarton.rgn"

def read_tail(path, size=500):
    try:
        with open(path, "rb") as f:
            f.seek(-size, 2)
            data = f.read()
            return data
    except Exception as e:
        return f"Error reading {path}: {e}"

def clean_decode(data):
    # Try to find the start of the XML (look for <)
    try:
        text = data.decode("utf-16le", errors="ignore")
        start = text.find("<")
        if start != -1:
            return text[start:]
        return text
    except:
        return str(data)

print("--- MRD_1S.rgn XML ---")
print(clean_decode(read_tail(file_mrd, 1000)))
print("\n--- Uladh_Dunbarton.rgn XML ---")
print(clean_decode(read_tail(file_dun, 1000)))
