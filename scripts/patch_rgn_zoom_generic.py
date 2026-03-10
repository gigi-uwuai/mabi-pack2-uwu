import os
import sys
import glob
import re
import shutil


TARGET_FARPLANE = "25000.000000"
TARGET_FOV = "100.000000"
TARGET_ZOOM_MAX = "25000.000000"


def find_rgn_files(args):
    """
    Resolve CLI arguments into a list of .rgn files.

    - If arg is a directory: recurse and collect *.rgn
    - If arg has wildcards: glob it
    - Else: if it's a file and endswith .rgn, use it
    """
    files = []

    if not args:
        print("Usage: python patch_rgn_zoom_generic.py <file_or_dir_or_glob> [...]")
        print("Examples:")
        print("  python patch_rgn_zoom_generic.py outputs\\zdunbyzoom\\data\\world\\Uladh_Dunbarton\\Uladh_Dunbarton.rgn")
        print("  python patch_rgn_zoom_generic.py outputs\\zbrizoom\\data\\world\\MRD_*\\*.rgn")
        print("  python patch_rgn_zoom_generic.py outputs\\zdunbyzoom")
        return files

    for arg in args:
        # Directory: recurse for .rgn
        if os.path.isdir(arg):
            for root, dirs, fnames in os.walk(arg):
                for name in fnames:
                    if name.lower().endswith(".rgn"):
                        files.append(os.path.join(root, name))
            continue

        # Glob pattern
        if any(ch in arg for ch in ["*", "?", "["]):
            for path in glob.glob(arg):
                if os.path.isfile(path) and path.lower().endswith(".rgn"):
                    files.append(path)
            continue

        # Direct file path
        if os.path.isfile(arg) and arg.lower().endswith(".rgn"):
            files.append(arg)
        else:
            print(f"WARNING: argument not found or not an .rgn file: {arg}")

    # Deduplicate while preserving order
    seen = set()
    unique_files = []
    for f in files:
        full = os.path.abspath(f)
        if full not in seen:
            seen.add(full)
            unique_files.append(full)

    return unique_files


def patch_rgn_file(path):
    """
    Patch a single .rgn file to:
      - farplane_n="...": farplane_n="25000.000000"
      - farplane_f="...": farplane_f="25000.000000"
      - fov="...":       fov="100.000000"
      - zoom_max="...":  zoom_max="25000.000000"

    We assume the XML <region ...> block is near the end of the file and is UTF-16LE,
    similar to the MRD and Dunbarton .rgn files.
    """
    print(f"\n--- Patching {path} ---")

    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        print(f"  ERROR: failed to read: {e}")
        return

    if not data:
        print("  (empty file, skipping)")
        return

    # Find <region in the file; support both UTF-16LE and single-byte encodings
    utf16_pattern = "<region".encode("utf-16le")
    ascii_pattern = b"<region"

    enc = None
    start = None

    idx_bytes = data.find(utf16_pattern)
    if idx_bytes != -1:
        enc = "utf-16le"
        start = idx_bytes
    else:
        idx_bytes = data.find(ascii_pattern)
        if idx_bytes != -1:
            enc = "latin-1"
            start = idx_bytes

    if enc is None or start is None:
        print("  WARNING: '<region' not found in file; deleting .rgn (no region XML)")
        try:
            os.remove(path)
            print(f"  Deleted unchanged .rgn: {path}")
        except Exception as e:
            print(f"  ERROR: failed to delete {path}: {e}")
        return

    prefix = data[:start]
    tail = data[start:]

    # Decode XML + trailing text in detected encoding
    text = tail.decode(enc, errors="ignore")

    idx = text.find("<region")
    if idx == -1:
        print("  WARNING: '<region' not found after decode; deleting .rgn (decode issue)")
        try:
            os.remove(path)
            print(f"  Deleted unchanged .rgn: {path}")
        except Exception as e:
            print(f"  ERROR: failed to delete {path}: {e}")
        return

    # Split: leading (pre-XML) part and the XML+trailing text
    leading_text = text[:idx]
    xml_text = text[idx:]

    original_xml = xml_text

    # Perform generic replacements
    def sub_once(label, pattern, replacement, s):
        new_s, count = re.subn(pattern, replacement, s)
        if count > 0:
            print(f"  ✓ {label}: {count} occurrence(s) replaced")
        else:
            print(f"  (no match) {label}")
        return new_s

    # farplane_n="..."
    xml_text = sub_once(
        "farplane_n",
        r'farplane_n="[^"]+"',
        f'farplane_n="{TARGET_FARPLANE}"',
        xml_text,
    )

    # farplane_f="..."
    xml_text = sub_once(
        "farplane_f",
        r'farplane_f="[^"]+"',
        f'farplane_f="{TARGET_FARPLANE}"',
        xml_text,
    )

    # fov="..."
    xml_text = sub_once(
        "fov",
        r'fov="[^"]+"',
        f'fov="{TARGET_FOV}"',
        xml_text,
    )

    # zoom_max="..."
    xml_text = sub_once(
        "zoom_max",
        r'zoom_max="[^"]+"',
        f'zoom_max="{TARGET_ZOOM_MAX}"',
        xml_text,
    )

    if xml_text == original_xml:
        print("  (no XML changes made; deleting .rgn)")
        try:
            os.remove(path)
            print(f"  Deleted unchanged .rgn: {path}")
        except Exception as e:
            print(f"  ERROR: failed to delete {path}: {e}")
        return

    # Rebuild tail bytes: leading_text + patched XML, using original encoding
    try:
        new_tail = (leading_text + xml_text).encode(enc)
    except Exception as e:
        print(f"  ERROR: failed to re-encode region XML as {enc}: {e}")
        return

    new_data = prefix + new_tail

    try:
        with open(path, "wb") as f:
            f.write(new_data)
    except Exception as e:
        print(f"  ERROR: failed to write patched file: {e}")
        return

    print(f"  ✓ Patched successfully (size {len(data)} -> {len(new_data)} bytes)")


def main():
    args = sys.argv[1:]

    # For any directory arguments, first delete folders whose name contains 'test'
    root_dirs = [os.path.abspath(a) for a in args if os.path.isdir(a)]
    for root in root_dirs:
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            base = os.path.basename(dirpath).lower()
            if "test" in base:
                try:
                    shutil.rmtree(dirpath)
                    print(f"Deleted test folder (pre-patch): {dirpath}")
                except Exception as e:
                    print(f"ERROR: failed to delete test folder {dirpath}: {e}")

    files = find_rgn_files(args)
    if not files:
        return

    print(f"Found {len(files)} .rgn file(s) to patch.")
    for f in files:
        patch_rgn_file(f)

    # After patching, for any directory arguments:
    root_dirs = [os.path.abspath(a) for a in args if os.path.isdir(a)]

    # 1) Delete any *.bak files
    for root in root_dirs:
        for dirpath, dirnames, filenames in os.walk(root):
            for name in filenames:
                if name.lower().endswith(".bak"):
                    bak_path = os.path.join(dirpath, name)
                    try:
                        os.remove(bak_path)
                        print(f"Deleted .bak file: {bak_path}")
                    except Exception as e:
                        print(f"ERROR: failed to delete .bak file {bak_path}: {e}")

    # 2) Remove any now-empty directories under directory arguments
    for root in root_dirs:
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            try:
                os.rmdir(dirpath)
                print(f"Removed empty directory: {dirpath}")
            except OSError:
                # Directory not empty or cannot be removed; ignore
                pass


if __name__ == "__main__":
    main()