#!/usr/bin/env python3
"""
Compiles the modular LaTeX report into a single monolithic .tex file.
"""

import re
from pathlib import Path

def main():
    docs_dir = Path(__file__).resolve().parent / "docs"
    master_tex = docs_dir / "Project_Report_EC499.tex"
    output_tex = docs_dir / "Project_Report_EC499_Monolithic.tex"

    content = master_tex.read_text(encoding="utf-8")

    def replace_input(match):
        rel_path = match.group(1).strip()
        if not rel_path.endswith(".tex"):
            rel_path += ".tex"
        target_file = docs_dir / rel_path
        if target_file.exists():
            print(f"[*] Inlining {rel_path} ({target_file.stat().st_size:,} bytes)")
            inlined = target_file.read_text(encoding="utf-8")
            return f"\n% === BEGIN INLINE: {rel_path} ===\n{inlined}\n% === END INLINE: {rel_path} ===\n"
        else:
            print(f"[-] Warning: {rel_path} not found!")
            return match.group(0)

    pattern = re.compile(r"\\input\{([^}]+)\}")
    monolithic = pattern.sub(replace_input, content)
    output_tex.write_text(monolithic, encoding="utf-8")
    print(f"[+] Successfully built {output_tex} ({output_tex.stat().st_size:,} bytes, {len(monolithic.splitlines())} lines)")

if __name__ == '__main__':
    main()
