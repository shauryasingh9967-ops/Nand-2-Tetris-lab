#!/usr/bin/env python3
"""
assembler.py — Two-pass Hack assembler (Nand to Tetris, Project 6)
Shaurya Vinay Singh, Roll No. 2501010296, ETCCNT301

Usage:
    python assembler.py Prog.asm            -> writes Prog.hack
    python assembler.py Prog.asm Out.hack    -> writes Out.hack

Pass 1: strip comments / blank lines, record every (LABEL) with its
        ROM instruction address.
Pass 2: translate each A- and C-instruction to 16-bit binary. New
        variables are allocated RAM addresses 16, 17, 18, ...

Extra feature (K mod 3 == 0): every discovered label and variable,
together with its address, is written to symbols.txt (next to the
output .hack file).
"""

import os
import sys

# ---------------------------------------------------------------- predefined symbols
PREDEFINED = {
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5, "R6": 6,
    "R7": 7, "R8": 8, "R9": 9, "R10": 10, "R11": 11, "R12": 12,
    "R13": 13, "R14": 14, "R15": 15,
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "SCREEN": 16384, "KBD": 24576,
}

# ---------------------------------------------------------------- comp (a + c1..c6)
# Commutative mnemonics are listed in both orders (e.g. D+A and A+D).
COMP = {
    "0":   "0101010", "1":   "0111111", "-1":  "0111010",
    "D":   "0001100", "A":   "0110000", "!D":  "0001101",
    "!A":  "0110001", "-D":  "0001111", "-A":  "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
    "A-1": "0110010", "D+A": "0000010", "A+D": "0000010",
    "D-A": "0010011", "A-D": "0000111", "D&A": "0000000",
    "A&D": "0000000", "D|A": "0010101", "A|D": "0010101",
    "M":   "1110000", "!M":  "1110001", "-M":  "1110011",
    "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
    "M+D": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "M&D": "1000000", "D|M": "1010101",
    "M|D": "1010101",
}

# ---------------------------------------------------------------- dest (d1 d2 d3)
# The dest field is order-independent (MD == DM, AM == MA, ...), so the
# bits are computed from the set of destination registers, not looked up.
def dest_bits(dest):
    """Return the 3 dest bits (A, D, M) for a dest mnemonic."""
    return ("1" if "A" in dest else "0") + \
           ("1" if "D" in dest else "0") + \
           ("1" if "M" in dest else "0")

# ---------------------------------------------------------------- jump (j1 j2 j3)
JUMP = {
    "":    "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}


def clean_lines(path):
    """Read an .asm file and return the list of meaningful instructions.

    Comments (//...) and blank lines are removed; surrounding
    whitespace is stripped. Label lines (LABEL) are kept so that
    pass 1 can record them.
    """
    instructions = []
    with open(path, "r") as f:
        for raw in f:
            line = raw.split("//")[0].strip()
            if line:
                instructions.append(line)
    return instructions


def assemble(input_path, output_path):
    """Assemble input_path (.asm) and write the binary to output_path (.hack).

    Returns (labels, variables): the symbol tables built during the
    two passes, used for symbols.txt.
    """
    lines = clean_lines(input_path)

    # ---- Pass 1: collect labels -------------------------------------------
    symbols = dict(PREDEFINED)
    labels = {}
    rom_address = 0
    for line in lines:
        if line.startswith("(") and line.endswith(")"):
            label = line[1:-1]
            labels[label] = rom_address
            symbols[label] = rom_address
        else:
            rom_address += 1

    # ---- Pass 2: translate -----------------------------------------------
    variables = {}
    next_var_address = 16
    binary_lines = []

    for line in lines:
        if line.startswith("(") and line.endswith(")"):
            continue  # label: no code generated

        if line.startswith("@"):
            # A-instruction: @value  or  @symbol
            symbol = line[1:]
            if symbol.isdigit():
                address = int(symbol)
            else:
                if symbol not in symbols:
                    symbols[symbol] = next_var_address
                    variables[symbol] = next_var_address
                    next_var_address += 1
                address = symbols[symbol]
            binary_lines.append("0" + format(address, "015b"))
        else:
            # C-instruction: dest=comp;jump
            dest = ""
            jump = ""
            comp = line
            if "=" in comp:
                dest, comp = comp.split("=", 1)
            if ";" in comp:
                comp, jump = comp.split(";", 1)
            comp_bits = COMP[comp]
            d_bits = dest_bits(dest)
            jump_bits = JUMP[jump]
            binary_lines.append("111" + comp_bits + d_bits + jump_bits)

    # The official Nand2Tetris assembler writes .hack files with CRLF
    # line terminators, so we do the same: the output is then
    # byte-for-byte identical to the official reference .hack files.
    with open(output_path, "w", newline="") as f:
        f.write("\r\n".join(binary_lines) + "\r\n")

    return labels, variables


def write_symbols_txt(symbols_path, labels, variables):
    """Write all labels and variables with their addresses to symbols.txt."""
    with open(symbols_path, "w") as f:
        f.write("# symbols.txt — labels and variables discovered by assembler.py\n")
        f.write("# (K mod 3 == 0 extra feature)\n")
        f.write("# format: <symbol> <address>\n\n")
        f.write("[labels]\n")
        for name in sorted(labels):
            f.write(f"{name} {labels[name]}\n")
        f.write("\n[variables]\n")
        for name in sorted(variables):
            f.write(f"{name} {variables[name]}\n")


def main(argv):
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python assembler.py Prog.asm [Prog.hack]")
        return 1

    input_path = argv[1]
    if len(argv) == 3:
        output_path = argv[2]
    else:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".hack"

    labels, variables = assemble(input_path, output_path)

    # Extra feature: symbols.txt next to the .hack output.
    symbols_path = os.path.join(os.path.dirname(output_path) or ".",
                                "symbols.txt")
    write_symbols_txt(symbols_path, labels, variables)

    print(f"Assembled {input_path} -> {output_path} "
          f"({len(labels)} labels, {len(variables)} variables)")
    print(f"Wrote {symbols_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
