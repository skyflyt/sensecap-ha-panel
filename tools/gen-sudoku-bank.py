#!/usr/bin/env python3
"""
Generate a bank of Sudoku puzzles and emit them as a Home Assistant template
sensor, so the panel never has to solve anything.

WHY OFF-DEVICE: generating a puzzle with a UNIQUE solution needs backtracking
plus a solution-counting pass over an 81-cell search space. That is minutes of
ESP32 time in the worst case, on the same core that drives LVGL — the panel
would appear frozen. Puzzles are static data; generate them once here, ship them
as strings, and the device only ever renders and validates.

Skylar asked for level + difficulty saved in HA (2026-08-25), which is also what
makes a half-finished grid survive the frequent reflashes.

Encoding: 81 characters, '0' = blank, row-major.

Run with WINDOWS python. Writes desk_pet_sudoku_bank.yaml next to the other
package files.
"""
from __future__ import annotations
import os, random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "desk_pet_sudoku_bank.yaml"))

# Givens per difficulty. Fewer givens is harder, but the honest driver of
# difficulty is which techniques a puzzle needs; given-count is a decent proxy
# and is the one every phone app uses.
DIFFS = {"Easy": 42, "Medium": 34, "Hard": 28}
PER_DIFF = 12


def solved_grid(rng: random.Random) -> list[int]:
    g = [0] * 81

    def ok(i: int, v: int) -> bool:
        r, c = divmod(i, 9)
        br, bc = (r // 3) * 3, (c // 3) * 3
        for k in range(9):
            if g[r * 9 + k] == v or g[k * 9 + c] == v:
                return False
            if g[(br + k // 3) * 9 + bc + k % 3] == v:
                return False
        return True

    def fill(i: int) -> bool:
        if i == 81:
            return True
        vals = list(range(1, 10))
        rng.shuffle(vals)
        for v in vals:
            if ok(i, v):
                g[i] = v
                if fill(i + 1):
                    return True
                g[i] = 0
        return False

    fill(0)
    return g


def count_solutions(g: list[int], cap: int = 2) -> int:
    """Stop as soon as `cap` solutions are found — we only ever need to know
    'exactly one' vs 'more than one'."""
    empties = [i for i, v in enumerate(g) if v == 0]
    if not empties:
        return 1
    # Most-constrained cell first; without this the count blows up on hard grids.
    def cands(i: int) -> list[int]:
        r, c = divmod(i, 9)
        br, bc = (r // 3) * 3, (c // 3) * 3
        used = set()
        for k in range(9):
            used.add(g[r * 9 + k]); used.add(g[k * 9 + c])
            used.add(g[(br + k // 3) * 9 + bc + k % 3])
        return [v for v in range(1, 10) if v not in used]

    i = min(empties, key=lambda x: len(cands(x)))
    total = 0
    for v in cands(i):
        g[i] = v
        total += count_solutions(g, cap - total)
        g[i] = 0
        if total >= cap:
            break
    return total


def carve(sol: list[int], givens: int, rng: random.Random) -> list[int] | None:
    p = sol[:]
    order = list(range(81))
    rng.shuffle(order)
    for i in order:
        if sum(1 for v in p if v) <= givens:
            break
        keep = p[i]
        p[i] = 0
        if count_solutions(p[:], 2) != 1:
            p[i] = keep          # removing it made the puzzle ambiguous
    return p if sum(1 for v in p if v) <= givens + 4 else None


def main() -> None:
    rng = random.Random(20260825)          # fixed seed: reproducible bank
    bank: dict[str, list[tuple[str, str]]] = {}
    for name, givens in DIFFS.items():
        got: list[tuple[str, str]] = []
        while len(got) < PER_DIFF:
            sol = solved_grid(rng)
            p = carve(sol, givens, rng)
            if p is None:
                continue
            got.append(("".join(map(str, p)), "".join(map(str, sol))))
            print(f"  {name} {len(got)}/{PER_DIFF}  givens={sum(1 for v in p if v)}")
        bank[name] = got

    lines = [
        "# Sudoku puzzle bank for the desk pet — GENERATED, do not hand-edit.",
        "# Source: tools/gen-sudoku-bank.py (fixed seed 20260825, reproducible).",
        "# Install as /homeassistant/packages/desk_pet_sudoku_bank.yaml",
        "#",
        "# Puzzles are generated OFF-DEVICE because building one with a unique",
        "# solution needs backtracking plus a solution-counting pass — minutes of",
        "# ESP32 time on the core that also drives LVGL. Every puzzle here was",
        f"# verified to have EXACTLY ONE solution. {PER_DIFF} per difficulty.",
        "#",
        "# 81 chars, row-major, '0' = blank.",
        "",
        "input_number:",
        "  pet_sudoku_index:",
        "    name: Pet Sudoku - Puzzle index",
        f"    min: 0",
        f"    max: {PER_DIFF - 1}",
        "    step: 1",
        "    mode: box",
        "    icon: mdi:grid",
        "",
        "input_select:",
        "  pet_sudoku_difficulty:",
        "    name: Pet Sudoku - Difficulty",
        "    options:",
    ]
    lines += [f"      - {d}" for d in DIFFS]
    lines += [
        "    icon: mdi:signal-cellular-2",
        "",
        "# NOTE: the per-difficulty saved boards live in the DAILY package",
        "# (desk_pet_sudoku_daily.yaml), which is also what the panel",
        "# actually reads. This file is the FALLBACK bank: it is served only when",
        "# no daily has been published — e.g. the workstation was off overnight.",
        "",
        "template:",
        "  - sensor:",
        "      - name: \"Pet Sudoku Bank Puzzle\"",
        "        unique_id: pet_sudoku_bank_puzzle",
        "        icon: mdi:grid",
        "        state: >-",
        "          {% set d = states('input_select.pet_sudoku_difficulty') %}",
        "          {% set i = states('input_number.pet_sudoku_index') | float(0) | int %}",
        "          {% set bank = {",
    ]
    for name, items in bank.items():
        lines.append(f"            '{name}': [")
        for pz, _ in items:
            lines.append(f"              '{pz}',")
        lines.append("            ],")
    lines += [
        "          } %}",
        "          {% set lst = bank.get(d, bank['Easy']) %}",
        "          {{ lst[i % (lst | length)] }}",
        "",
        "      - name: \"Pet Sudoku Bank Solution\"",
        "        unique_id: pet_sudoku_bank_solution",
        "        icon: mdi:grid-off",
        "        state: >-",
        "          {% set d = states('input_select.pet_sudoku_difficulty') %}",
        "          {% set i = states('input_number.pet_sudoku_index') | float(0) | int %}",
        "          {% set bank = {",
    ]
    for name, items in bank.items():
        lines.append(f"            '{name}': [")
        for _, sol in items:
            lines.append(f"              '{sol}',")
        lines.append("            ],")
    lines += [
        "          } %}",
        "          {% set lst = bank.get(d, bank['Easy']) %}",
        "          {{ lst[i % (lst | length)] }}",
        "",
        "script:",
        "  # Next puzzle at the current difficulty. Wraps at the end of the bank.",
        "  indicator_pet_sudoku_next:",
        "    alias: Indicator Pet - Sudoku next puzzle",
        "    icon: mdi:grid",
        "    mode: single",
        "    sequence:",
        "      - action: input_number.set_value",
        "        target: { entity_id: input_number.pet_sudoku_index }",
        "        data:",
        f"          value: \"{{{{ ((states('input_number.pet_sudoku_index')|float(0)|int) + 1) % {PER_DIFF} }}}}\"",
        "      - delay: { milliseconds: 400 }",
        "      # Board entity follows the selected difficulty.",
        "      - action: input_text.set_value",
        "        target:",
        "          entity_id: >-",
        "            {{ 'input_text.pet_sudoku_state_' ~",
        "               {'Easy':'e','Medium':'m','Hard':'h'}.get(",
        "                 states('input_select.pet_sudoku_difficulty'),'e') }}",
        "        data:",
        "          value: \"{{ states('sensor.pet_sudoku_puzzle') }}\"",
        "",
        "  # Cycle Easy -> Medium -> Hard and deal a fresh grid at the new level.",
        "  indicator_pet_sudoku_difficulty:",
        "    alias: Indicator Pet - Sudoku difficulty",
        "    icon: mdi:signal-cellular-2",
        "    mode: single",
        "    sequence:",
        "      - action: input_select.select_next",
        "        target: { entity_id: input_select.pet_sudoku_difficulty }",
        "        data: { cycle: true }",
        "      - delay: { milliseconds: 400 }",
        "      # Board entity follows the selected difficulty.",
        "      - action: input_text.set_value",
        "        target:",
        "          entity_id: >-",
        "            {{ 'input_text.pet_sudoku_state_' ~",
        "               {'Easy':'e','Medium':'m','Hard':'h'}.get(",
        "                 states('input_select.pet_sudoku_difficulty'),'e') }}",
        "        data:",
        "          value: \"{{ states('sensor.pet_sudoku_puzzle') }}\"",
        "",
        "  # Restart the current grid.",
        "  indicator_pet_sudoku_reset:",
        "    alias: Indicator Pet - Sudoku reset",
        "    icon: mdi:restore",
        "    mode: single",
        "    sequence:",
        "      # Board entity follows the selected difficulty.",
        "      - action: input_text.set_value",
        "        target:",
        "          entity_id: >-",
        "            {{ 'input_text.pet_sudoku_state_' ~",
        "               {'Easy':'e','Medium':'m','Hard':'h'}.get(",
        "                 states('input_select.pet_sudoku_difficulty'),'e') }}",
        "        data:",
        "          value: \"{{ states('sensor.pet_sudoku_puzzle') }}\"",
        "",
    ]
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
