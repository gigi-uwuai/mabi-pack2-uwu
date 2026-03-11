# Mabinogi Pack Utilities 2

This repository is based on the original [`regomne/mabi-pack2`](https://github.com/regomne/mabi-pack2) project. This version is a maintained derivative/fork with additional changes, while keeping credit to the original work.

New pack utilities for Mabinogi.

Works on *.it* packages.

Can run both in Windows and \*nix/MacOS. Includes a Command-Line Interface (CLI) and a Graphical User Interface (GUI).

## Build

Use rust 1.59 or above.

Build both the CLI and GUI executables:
```bash
cargo build --release
```

## Setup & Encryption Salts

Both the CLI and GUI require a `salt_keys.json` file in the same directory as the executable to decrypt or encrypt `.it` packages.
If you do not have one, create it based on `salt_keys.example.json` containing the specific salt keys for your region's client:

```json
{
  "salt_keys": [
    "YourSaltHere"
  ]
}
```

## Usage (GUI)

A graphical interface is included for easier interaction. You can build and run it directly using Cargo:
```bash
cargo run --release --bin mabi-pack2-gui
```
Or, if you have already built it using the command above, you can launch the executable directly:
```bash
./target/release/mabi-pack2-gui
```

## Usage (CLI)

```
USAGE:
    mabi-pack2 [SUBCOMMAND]

OPTIONS:
    -h, --help       Print help information
    -V, --version    Print version information

SUBCOMMANDS:
    extract    Extract a .it pack (or all .it packs in a folder)
    help       Print this message or the help of the given subcommand(s)
    list       Output the file list of a .it pack (or all .it packs in a folder)
    pack       Create a .it pack
```

### Examples

**Extract all `.xml` and `.txt` files from a pack:**
```bash
mabi-pack2 extract -i D:\Mabinogi\package\data_00788.it -o D:\data --filter "\.xml" --filter "\.txt"
```

**Batch extract from ALL packages in a folder:**
```bash
mabi-pack2 extract -i D:\Mabinogi\package -o D:\Mabi_Extracted -f "(?i)chick.*wav"
```

**List all files of a pack or folder:**
```bash
mabi-pack2 list -i D:\Mabinogi\package\data_00000.it
mabi-pack2 list -i D:\Mabinogi\package
```

**Pack files to a .it file (Requires `-s` parameter or first key in JSON):**
```bash
mabi-pack2 pack -i D:\Mabinogi\pkg -o custom_01.it
mabi-pack2 pack -i D:\Mabinogi\pkg -o custom_01.it -s "CuAVPMZx:E96:(Rxdw"
```

### Important packing rules

When creating a new `.it` file, keep these requirements in mind:

- **The output filename should follow this exact format:**
  - `<name>_<number>.it`
  - `<name>` must be a **single name part** (no extra underscores)
  - `<name>` must start with a letter after `d` — for example `e`, `f`, `g`, etc.
  - where `<number>` is **1 to 5 digits** (`0` to `99999`)
- Examples:
  - Valid: `eapple_01.it`, `zoom_711.it`, `uppercut_0.it`
  - Invalid: `apple_01.it`, `dapple_01.it`, `e_chick_01.it`
- **The input folder must include a top-level folder containing `data/` inside it.**
  - Correct structure: `test/data/sound/chick.wav`
  - Incorrect structure: `data/sound/chick.wav`

Example:

```text
test/
└── data/
    └── sound/
        └── chick.wav
```

*Note:* Renaming of \*.it files is not allowed, or extracting and listing will fail.

## License

This program is distributed under the MIT License.
