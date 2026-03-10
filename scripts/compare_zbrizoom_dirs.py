import os
import sys
import hashlib
import difflib

BASE_DIR = r"e:\Mabinogi_Mods_Apps\mabi-pack2"
LEFT_DEFAULT = os.path.join(BASE_DIR, "outputs", "zbrizoom")
RIGHT_DEFAULT = os.path.join(BASE_DIR, "outputs", "un-modded-zbrizoom")


def collect_files(root):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            rel = rel.replace("\\", "/")
            files[rel] = full
    return files


def sha256(path, block_size=65536):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def try_read_text(path):
    # Try utf-16le first (common for these game files), then utf-8
    for enc in ("utf-16le", "utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.readlines(), enc
        except Exception:
            continue
    return None, None


def main():
    if len(sys.argv) >= 3:
        left_root = sys.argv[1]
        right_root = sys.argv[2]
    else:
        left_root = LEFT_DEFAULT
        right_root = RIGHT_DEFAULT

    print(f"Comparing:")
    print(f"  LEFT (modded):   {left_root}")
    print(f"  RIGHT (unmodded): {right_root}")
    print()

    if not os.path.isdir(left_root):
        print(f"ERROR: Left directory does not exist: {left_root}")
        return
    if not os.path.isdir(right_root):
        print(f"ERROR: Right directory does not exist: {right_root}")
        return

    left_files = collect_files(left_root)
    right_files = collect_files(right_root)

    left_only = sorted(set(left_files.keys()) - set(right_files.keys()))
    right_only = sorted(set(right_files.keys()) - set(left_files.keys()))
    common = sorted(set(left_files.keys()) & set(right_files.keys()))

    print("=== Files only in LEFT (modded) ===")
    for rel in left_only:
        print(rel)
    if not left_only:
        print("(none)")
    print()

    print("=== Files only in RIGHT (unmodded) ===")
    for rel in right_only:
        print(rel)
    if not right_only:
        print("(none)")
    print()

    print("=== Files present in both ===")
    print("(showing only changed files)")
    print()

    for rel in common:
        left_path = left_files[rel]
        right_path = right_files[rel]

        left_size = os.path.getsize(left_path)
        right_size = os.path.getsize(right_path)
        left_hash = sha256(left_path)
        right_hash = sha256(right_path)

        if left_hash == right_hash:
            continue  # identical

        print(f"--- CHANGED: {rel} ---")
        print(f"  size: {left_size} (left) vs {right_size} (right)")
        print(f"  sha256:")
        print(f"    left : {left_hash}")
        print(f"    right: {right_hash}")

        # Try to show text diff for small-ish files
        max_text_bytes = 512 * 1024  # 512 KB
        if left_size <= max_text_bytes and right_size <= max_text_bytes:
            left_lines, left_enc = try_read_text(left_path)
            right_lines, right_enc = try_read_text(right_path)
            if left_lines is not None and right_lines is not None:
                print(f"  text diff (left enc={left_enc}, right enc={right_enc}):")
                diff = difflib.unified_diff(
                    right_lines,
                    left_lines,
                    fromfile=f"unmodded/{rel}",
                    tofile=f"modded/{rel}",
                    lineterm="",
                )
                # Limit diff lines to avoid insane output
                max_diff_lines = 200
                count = 0
                for line in diff:
                    print(line.rstrip("\n"))
                    count += 1
                    if count >= max_diff_lines:
                        print("  ... (diff truncated)")
                        break
            else:
                print("  (binary or unsupported encoding; text diff not shown)")
        else:
            print("  (file too large for text diff)")

        print()


if __name__ == "__main__":
    main()