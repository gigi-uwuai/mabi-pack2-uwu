import os
import glob
import re

directory = r"e:\Mabinogi_Mods_Apps\mabi-pack2\outputs\zdunbyzoom\data\world\Uladh_Dunbarton"
xml_files = glob.glob(os.path.join(directory, "region_variation_*.xml"))

# The key property from the working MRD mod
unlimited_sight = '\t\t<unlimitedSight enable="true"/>\n'

for file_path in xml_files:
    try:
        with open(file_path, "r", encoding="utf-16le") as f:
            content = f.read()
        
        # Check if unlimitedSight already exists
        if "unlimitedSight" in content:
            print(f"Already has unlimitedSight: {os.path.basename(file_path)}")
            continue
        
        # Find <property> section and add the line
        # Look for <property> followed by </property>, possibly with content between
        if "<property>" in content:
            # Add unlimitedSight after the opening <property> tag
            new_content = re.sub(
                r"(<property>)",
                r"\1\n" + unlimited_sight,
                content
            )
            
            if content != new_content:
                with open(file_path, "w", encoding="utf-16le") as f:
                    f.write(new_content)
                print(f"Added unlimitedSight to: {os.path.basename(file_path)}")
            else:
                print(f"No change for: {os.path.basename(file_path)}")
        else:
            print(f"No <property> section in: {os.path.basename(file_path)}")
            
    except Exception as e:
        print(f"Error processing {os.path.basename(file_path)}: {e}")
