#!/usr/bin/env python3
"""Fail CI on proof escape hatches; Lean still performs the actual proof check."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in [*ROOT.glob("*.lean"), *ROOT.glob("LeanPose/*.lean"), *ROOT.glob("tests/*.lean")]:
    # Source comments are excluded; this simple guard complements, not replaces, Lean.
    source = re.sub(r"/\-.*?\-/", "", path.read_text(), flags=re.S)
    source = re.sub(r"--[^\n]*", "", source)
    if re.search(r"\b(sorry|admit|axiom|native_decide)\b", source):
        raise SystemExit(f"proof escape hatch in {path.relative_to(ROOT)}")
print("No proof placeholders or custom axioms found.")
