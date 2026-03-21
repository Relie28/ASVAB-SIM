#!/usr/bin/env python3
"""
ASVAB SIM — Formula Lab Unit Tests
=====================================
Runs against /Users/aurelienessome/Desktop/ASVAB SIM/index.html.

A Node.js sub-process extracts FORMULA_CARDS and _flGenLevelQ directly from
the HTML source, generates N_RUNS sessions per card × level, and pipes the
results back as JSON.  All assertion logic lives in Python.

Test suites
-----------
  TestCardStructure         — every FORMULA_CARD has required fields
  TestAppQAnswerCorrectness — every appQs[i].opts[ans] is in-range and non-empty
  TestVarFormat             — every var entry contains an '=' separator
  TestQGenStructure         — every generated question has valid fields / ans in range
  TestQGenAnswerCorrectness — opts[ans] matches the semantically correct answer
                              per type: R→formula, V_→meaning, C_→symbol, A→appQ answer
  TestQGenUniqueness        — all FL_SESSION_SIZE types within one session are distinct
  TestQGenHintPolicy        — formula hint present at L4 only; absent at L5/L6/L7
  TestQGenLevelAdaptivity   — each level exposes its expected PRIMARY question type
  TestQGenCrossLevel        — L1 and L6 sessions expose categorically different types

Usage
-----
  python3 test_formula_lab.py        # brief summary
  python3 test_formula_lab.py -v     # verbose per-test output
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HTML_PATH        = '/Users/aurelienessome/Desktop/ASVAB SIM/index.html'
N_RUNS           = 10    # runs per card × level — catches probabilistic failures
FL_MASTERY_LEVEL = 7
FL_SESSION_SIZE  = 5

# ─────────────────────────────────────────────────────────────────────────────
# Node.js runner — builds a minimal JS file and captures generated questions
# ─────────────────────────────────────────────────────────────────────────────

def _build_runner_script(html: str) -> str:
    """
    Extracts three JS sections from index.html:
      1. const FORMULA_CARDS = [...]
      2. const FL_MASTERY_LEVEL / FL_SESSION_SIZE / FL_PASS_THRESHOLD
      3. function _flGenLevelQ(...)
    Wraps them in a Node.js runner that serialises all sessions to stdout.
    """
    # ── 1. _FL_SVG helper object (FORMULA_CARDS references it) ────────────────
    svg_start = html.index('\nconst _FL_SVG')
    svg_end   = html.index('\n};\n', svg_start) + 4

    # ── 2. FORMULA_CARDS array ─────────────────────────────────────────────────
    fc_start = html.index('\nconst FORMULA_CARDS')
    fc_end   = html.index('\n];\n', fc_start) + 4

    # ── 3. FL constants only (FL_MASTERY_LEVEL / FL_SESSION_SIZE / FL_PASS_THRESHOLD) ──
    fl_start = html.index('\nconst FL_MASTERY_LEVEL')
    fl_end   = html.index('\nconst _fl', fl_start)   # stop before the runtime object

    # ── 3. _flGenLevelQ function (find its closing brace by counting depth) ──
    gen_start = html.index('\nfunction _flGenLevelQ')
    depth = 0
    i = gen_start
    while i < len(html):
        if html[i] == '{':
            depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    gen_end = i + 1

    runner = (
        "'use strict';\n"
        + html[svg_start:svg_end] + "\n"
        + html[fc_start:fc_end] + "\n"
        + html[fl_start:fl_end] + "\n"
        + html[gen_start:gen_end] + "\n"
        + f"""
// ── Generate N_RUNS sessions per card × currentLevel ──────────────────────
const N_RUNS = {N_RUNS};
const output = {{ cards: FORMULA_CARDS, sessions: {{}} }};

for (const card of FORMULA_CARDS) {{
  output.sessions[card.id] = {{}};
  for (let currentLevel = 0; currentLevel < FL_MASTERY_LEVEL; currentLevel++) {{
    output.sessions[card.id][currentLevel] = [];
    for (let run = 0; run < N_RUNS; run++) {{
      try {{
        const qs = _flGenLevelQ(card.id, currentLevel);
        output.sessions[card.id][currentLevel].push(qs);
      }} catch (e) {{
        output.sessions[card.id][currentLevel].push({{ error: e.message }});
      }}
    }}
  }}
}}

process.stdout.write(JSON.stringify(output));
"""
    )
    return runner


def _load_generated_data() -> dict:
    """Run the Node.js generator and return the parsed JSON output."""
    html = open(HTML_PATH, encoding='utf-8').read()
    script = _build_runner_script(html)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(script)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ['node', tmp_path],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Node.js runner failed (exit {result.returncode}):\n"
                f"{result.stderr[:2000]}"
            )
        if not result.stdout.strip():
            raise RuntimeError("Node.js runner produced no output.")
        return json.loads(result.stdout)
    finally:
        os.unlink(tmp_path)


# Load once at module level — shared by all test classes
try:
    _DATA     = _load_generated_data()
    _CARDS    = _DATA['cards']
    _SESSIONS = _DATA['sessions']           # card_id → str(0..6) → list[list[q]]
    _BY_ID    = {c['id']: c for c in _CARDS}
except Exception as _load_err:
    print(f"\nFATAL: Could not load Formula Lab data:\n  {_load_err}", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _loc(card_id: str, extra: str = '') -> str:
    card = _BY_ID.get(card_id, {})
    name = card.get('name', card_id)
    s = f"[{card_id}] {name}"
    return s + (f" — {extra}" if extra else '')


def _strip_html(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', str(s))).strip()


def _valid_var_syms(card: dict) -> list:
    """
    Returns the list of non-ambiguous var symbols for a card —
    i.e. symbols that appear exactly once as a left-hand side across all var lines.
    Matches the dedup logic in _flGenLevelQ.
    """
    counts = {}
    for v in card.get('vars', []):
        ei = str(v).find('=')
        if ei >= 0:
            s = v[:ei].strip()
            counts[s] = counts.get(s, 0) + 1
    return [s for s, n in counts.items() if n == 1]


def _is_unit_sym(sym: str) -> bool:
    return bool(re.match(r'^\d', sym) or re.match(r'^[A-Za-z]+ ', sym))


def _has_comp_syms(card: dict) -> bool:
    """True if the card has at least one algebraic symbol that can produce C_ questions."""
    formula = card.get('formula', '')
    for sym in _valid_var_syms(card):
        if len(sym) > 4 or _is_unit_sym(sym):
            continue
        escaped = re.escape(sym)
        if re.search(r'(?<![A-Za-z])' + escaped + r'(?![A-Za-z])', formula):
            return True
    return False


def _count_v_types(card: dict) -> int:
    """Number of V_ questions the card can generate (mirrors Vs() filter logic)."""
    vars_list = card.get('vars', [])
    valid = _valid_var_syms(card)
    count = 0
    for sym in valid:
        wrongs = [
            v[v.find('=') + 1:].strip()
            for v in vars_list
            if '=' in v and v[:v.find('=')].strip() != sym
        ]
        if len(wrongs) >= 2:
            count += 1
    return count


# ─────────────────────────────────────────────────────────────────────────────
# Pass 1 — Card structure
# ─────────────────────────────────────────────────────────────────────────────

def _make_card_structure_test(card: dict):
    def test(self):
        cid = card.get('id', '???')
        loc = _loc(cid)
        self.assertTrue(str(cid).strip(),
            f"{loc}\n  → 'id' is missing or empty")
        self.assertTrue(card.get('name', '').strip(),
            f"{loc}\n  → 'name' is missing or empty")
        self.assertTrue(card.get('formula', '').strip(),
            f"{loc}\n  → 'formula' is missing or empty")
        self.assertIsInstance(card.get('vars'), list,
            f"{loc}\n  → 'vars' must be a list")
        self.assertGreater(len(card.get('vars', [])), 0,
            f"{loc}\n  → 'vars' is empty — every card needs at least one variable line")
        self.assertTrue(card.get('tip', '').strip(),
            f"{loc}\n  → 'tip' is missing or empty")
        self.assertTrue(card.get('ex', '').strip(),
            f"{loc}\n  → 'ex' is missing or empty")
        self.assertIsInstance(card.get('appQs'), list,
            f"{loc}\n  → 'appQs' must be a list (can be empty)")
        self.assertTrue(card.get('svg', '').strip(),
            f"{loc}\n  → 'svg' is missing or empty")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 2 — appQ answer correctness
# ─────────────────────────────────────────────────────────────────────────────

def _make_appq_test(card: dict, qi: int, appq: dict):
    def test(self):
        cid  = card['id']
        loc  = _loc(cid, f"appQs[{qi}]")
        opts = appq.get('opts', [])
        ans  = appq.get('ans')

        self.assertTrue(_strip_html(appq.get('q', '')),
            f"{loc}\n  → question text is empty")
        self.assertIsInstance(opts, list,
            f"{loc}\n  → opts must be a list")
        self.assertGreaterEqual(len(opts), 2,
            f"{loc}\n  → needs at least 2 options, got {len(opts)}")
        self.assertIsInstance(ans, int,
            f"{loc}\n  → ans must be an integer, got {type(ans)}")
        self.assertGreaterEqual(ans, 0,
            f"{loc}\n  → ans={ans} is negative")
        self.assertLess(ans, len(opts),
            f"{loc}\n  → ans={ans} out of range (opts has {len(opts)} items, "
            f"valid 0–{len(opts) - 1})")
        self.assertTrue(str(opts[ans]).strip(),
            f"{loc}\n  → opts[ans={ans}] is empty — correct answer is blank")
        self.assertTrue(appq.get('exp', '').strip(),
            f"{loc}\n  → explanation 'exp' is empty")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 3 — var format
# ─────────────────────────────────────────────────────────────────────────────

def _make_var_format_test(card: dict):
    def test(self):
        loc = _loc(card['id'])
        # Only validate entries that Vs() actually parses — those containing '='.
        # Note-style entries without any '=' (e.g. 'Positive m → goes up left to right')
        # are intentionally skipped by the generator and don't need to be flagged.
        parsed = [v for v in card.get('vars', []) if '=' in str(v)]
        bad = []
        for v in parsed:
            ei = v.find('=')
            sym  = v[:ei].strip()
            mean = v[ei + 1:].strip()
            if not sym:
                bad.append(f"'{v}'  (left side of '=' is empty)")
            elif not mean:
                bad.append(f"'{v}'  (right side of '=' is empty)")
        self.assertFalse(bad,
            f"{loc}\n  → malformed var definitions (= present but side is empty):\n"
            + '\n'.join(f'    {b}' for b in bad))
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 4 — generated question structural validity
# ─────────────────────────────────────────────────────────────────────────────

def _make_qgen_structure_test(card: dict, current_level: int):
    def test(self):
        cid   = card['id']
        label = f"L{current_level + 1}"
        runs  = _SESSIONS[cid][str(current_level)]

        for ri, session in enumerate(runs):
            loc = _loc(cid, f"{label} run={ri + 1}")

            if isinstance(session, dict) and 'error' in session:
                self.fail(f"{loc}\n  → _flGenLevelQ threw: {session['error']}")

            self.assertIsInstance(session, list,
                f"{loc}\n  → session is not a list: {type(session)}")
            self.assertEqual(len(session), FL_SESSION_SIZE,
                f"{loc}\n  → expected {FL_SESSION_SIZE} questions, got {len(session)}\n"
                f"  The generator must always produce exactly {FL_SESSION_SIZE} questions.")

            for qi, q in enumerate(session):
                qloc = f"{loc} q[{qi}]"
                self.assertTrue(q.get('type', '').strip(),
                    f"{qloc}\n  → 'type' field is missing or empty")
                self.assertTrue(_strip_html(q.get('q', '')),
                    f"{qloc}\n  → question text 'q' is empty")
                opts = q.get('opts', [])
                self.assertGreaterEqual(len(opts), 2,
                    f"{qloc}\n  → needs at least 2 options, got {len(opts)}")
                ans = q.get('ans')
                self.assertIsInstance(ans, int,
                    f"{qloc}\n  → ans must be an integer, got {type(ans)}")
                self.assertGreaterEqual(ans, 0,
                    f"{qloc}\n  → ans={ans} is negative")
                self.assertLess(ans, len(opts),
                    f"{qloc}\n  → ans={ans} out of range "
                    f"(opts has {len(opts)} items, valid 0–{len(opts) - 1})")
                self.assertTrue(str(opts[ans]).strip(),
                    f"{qloc}\n  → opts[ans={ans}] is empty — correct answer is blank")
                self.assertTrue(q.get('exp', '').strip(),
                    f"{qloc}\n  → explanation 'exp' is empty")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 5 — generated question answer correctness per type
# ─────────────────────────────────────────────────────────────────────────────

def _make_qgen_answer_test(card: dict, current_level: int):
    """
    Validates opts[ans] is the SEMANTICALLY CORRECT value for each type:
      R1 / R3 / R4  → opts[ans] == card.formula
      R2            → opts[ans] == card.name
      V_SYM         → opts[ans] == the meaning for SYM from card.vars
      C_SYM         → opts[ans] == SYM (the symbol itself)
      A{i}          → opts[ans] == appQs[i].opts[appQs[i].ans]
    """
    def test(self):
        cid     = card['id']
        label   = f"L{current_level + 1}"
        formula = card.get('formula', '')
        name    = card.get('name', '')
        appqs   = card.get('appQs', [])
        runs    = _SESSIONS[cid][str(current_level)]

        # Build sym→meaning lookup from vars
        meanings = {}
        for v in card.get('vars', []):
            ei = str(v).find('=')
            if ei >= 0:
                meanings[v[:ei].strip()] = v[ei + 1:].strip()

        for ri, session in enumerate(runs):
            if not isinstance(session, list):
                continue
            for qi, q in enumerate(session):
                qtype = q.get('type', '')
                opts  = q.get('opts', [])
                ans   = q.get('ans', -1)
                if ans < 0 or ans >= len(opts):
                    continue    # structural failure already caught in Pass 4
                chosen = opts[ans]
                loc = _loc(cid, f"{label} run={ri + 1} q[{qi}] type={qtype}")

                if qtype in ('R1', 'R3', 'R4'):
                    self.assertEqual(chosen, formula,
                        f"{loc}\n"
                        f"  → opts[ans] should be the card formula:\n"
                        f"    expected: '{formula}'\n"
                        f"    got:      '{chosen}'\n"
                        f"  opts={opts}")

                elif qtype == 'R2':
                    self.assertEqual(chosen, name,
                        f"{loc}\n"
                        f"  → opts[ans] should be the card name:\n"
                        f"    expected: '{name}'\n"
                        f"    got:      '{chosen}'\n"
                        f"  opts={opts}")

                elif qtype.startswith('V_'):
                    sym = qtype[2:]
                    expected = meanings.get(sym)
                    if expected is not None:
                        self.assertEqual(chosen, expected,
                            f"{loc}\n"
                            f"  → V_question for symbol '{sym}': opts[ans] should be the meaning:\n"
                            f"    expected: '{expected}'\n"
                            f"    got:      '{chosen}'\n"
                            f"  opts={opts}")

                elif qtype.startswith('C_'):
                    sym = qtype[2:]
                    self.assertEqual(chosen, sym,
                        f"{loc}\n"
                        f"  → C_question (complete-the-formula) for symbol '{sym}':\n"
                        f"    opts[ans] should be the SYMBOL itself ('{sym}')\n"
                        f"    got: '{chosen}'\n"
                        f"  opts={opts}")

                elif qtype.startswith('A') and qtype[1:].isdigit():
                    idx = int(qtype[1:])
                    if idx < len(appqs):
                        aq       = appqs[idx]
                        expected = aq['opts'][aq['ans']]
                        self.assertEqual(chosen, expected,
                            f"{loc}\n"
                            f"  → A-question (appQs[{idx}]): opts[ans] should be:\n"
                            f"    expected: '{expected}'\n"
                            f"    got:      '{chosen}'\n"
                            f"  opts={opts}")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 6 — intra-session type uniqueness
# ─────────────────────────────────────────────────────────────────────────────

def _make_qgen_uniqueness_test(card: dict, current_level: int):
    def test(self):
        cid   = card['id']
        label = f"L{current_level + 1}"
        runs  = _SESSIONS[cid][str(current_level)]

        for ri, session in enumerate(runs):
            if not isinstance(session, list):
                continue
            types = [q.get('type') for q in session]
            loc   = _loc(cid, f"{label} run={ri + 1}")
            self.assertEqual(len(types), len(set(types)),
                f"{loc}\n"
                f"  → DUPLICATE question types in one session: {types}\n"
                f"  The user is seeing the same question framing twice in a single round.\n"
                f"  Each type key must appear at most once per session.")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 7 — hint policy
# ─────────────────────────────────────────────────────────────────────────────

def _make_qgen_hint_policy_test(card: dict, current_level: int):
    """
    Formula hint rules:
      L4  (currentLevel=3) : A-type Qs MUST carry hint=card.formula.
      L5+ (currentLevel≥4) : A-type Qs MUST have hint=null.
      L1–L2 (currentLevel≤1): A-type Qs must NOT appear when the card has enough
                               R+V types to fill FL_SESSION_SIZE without fallback.
    """
    def test(self):
        cid     = card['id']
        label   = f"L{current_level + 1}"
        formula = card.get('formula', '')
        runs    = _SESSIONS[cid][str(current_level)]

        if not card.get('appQs'):
            return  # no appQs → no A-type Qs → nothing to test

        # Cards with 4 R-types + ≥1 V-type have ≥5 non-A candidates at L1/L2.
        # For those cards, A-types in L1/L2 are a bug, not a fallback.
        rich_enough_for_recognition_only = _count_v_types(card) >= 1

        for ri, session in enumerate(runs):
            if not isinstance(session, list):
                continue
            a_qs = [q for q in session if q.get('type', '').startswith('A')
                    and q.get('type', '')[1:].isdigit()]
            loc  = _loc(cid, f"{label} run={ri + 1}")

            # ── L1 / L2: recognition-only levels ──────────────────────────────
            if current_level <= 1 and rich_enough_for_recognition_only:
                self.assertEqual(len(a_qs), 0,
                    f"{loc}\n"
                    f"  → Application (A-type) questions appeared at {label}.\n"
                    f"  L1 and L2 are recognition levels — A-types must not appear\n"
                    f"  when the card has enough R/V content to fill {FL_SESSION_SIZE} slots.\n"
                    f"  Session types: {[q['type'] for q in session]}")

            # ── L4: application WITH hint ──────────────────────────────────────
            elif current_level == 3:
                for q in a_qs:
                    self.assertEqual(q.get('hint'), formula,
                        f"{loc} type={q['type']}\n"
                        f"  → A-type at L4 MUST show the formula as a hint.\n"
                        f"  Expected hint='{formula}'\n"
                        f"  Got     hint={q.get('hint')!r}\n"
                        f"  The formula hint is the scaffolding that distinguishes L4 from L5+.")

            # ── L5 / L6 / L7: application WITHOUT hint ────────────────────────
            elif current_level >= 4:
                for q in a_qs:
                    self.assertIsNone(q.get('hint'),
                        f"{loc} type={q['type']}\n"
                        f"  → A-type at {label} must NOT show the formula as a hint.\n"
                        f"  Got hint={q.get('hint')!r}\n"
                        f"  Formula hints are only permitted at L4 — at {label} the\n"
                        f"  user must recall the formula from memory.")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 8 — level adaptivity (primary type presence)
# ─────────────────────────────────────────────────────────────────────────────

def _make_qgen_adaptivity_test(card: dict, current_level: int):
    """
    Verifies that every session at a given level contains the expected PRIMARY
    question type.  Assertions are gated on whether the card actually has the
    content needed to satisfy that type.

      L1 (0): ≥1 R-type       — always (R1–R4 always available)
      L2 (1): R3 or R4        — always (harder-distractor recognition)
      L3 (2): ≥1 V_-type      — only if card has ≥2 valid non-ambiguous vars
      L4 (3): ≥1 A-type       — only if card has appQs
      L5 (4): ≥1 C_-type      — only if card has algebraic symbols in formula
      L6 (5): ≥1 A-type       — only if card has appQs
      L7 (6): ≥1 A-type       — only if card has appQs
    """
    def test(self):
        cid       = card['id']
        label     = f"L{current_level + 1}"
        has_appqs = bool(card.get('appQs'))
        n_v       = _count_v_types(card)
        has_comp  = _has_comp_syms(card)
        runs      = _SESSIONS[cid][str(current_level)]

        for ri, session in enumerate(runs):
            if not isinstance(session, list):
                continue
            types = [q.get('type', '') for q in session]
            r_types = [t for t in types if t in ('R1', 'R2', 'R3', 'R4')]
            v_types = [t for t in types if t.startswith('V_')]
            a_types = [t for t in types if t.startswith('A') and t[1:].isdigit()]
            c_types = [t for t in types if t.startswith('C_')]
            loc = _loc(cid, f"{label} run={ri + 1} types={types}")

            if current_level == 0:           # L1 — recognition with SVG
                self.assertTrue(r_types,
                    f"{loc}\n"
                    f"  → L1 must include at least one recognition (R) question.\n"
                    f"  R-types are always available (R1–R4 need no special card content).")

            elif current_level == 1:         # L2 — harder recognition, no SVG
                self.assertTrue(any(t in ('R3', 'R4') for t in types),
                    f"{loc}\n"
                    f"  → L2 must include R3 or R4 (harder distractors, no SVG shown).\n"
                    f"  Got types: {types}")

            elif current_level == 2 and n_v >= 2:   # L3 — variable identification
                self.assertTrue(v_types,
                    f"{loc}\n"
                    f"  → L3 must include at least one V_-type (variable identification).\n"
                    f"  This card has {n_v} valid var symbols. V_-types are the primary\n"
                    f"  focus at L3 — the user should be identifying what each symbol means.\n"
                    f"  Got types: {types}")

            elif current_level == 3 and has_appqs:   # L4 — apply with hint
                self.assertTrue(a_types,
                    f"{loc}\n"
                    f"  → L4 must include at least one A-type (application with hint).\n"
                    f"  This card has {len(card['appQs'])} appQ(s). At L4 the user should\n"
                    f"  be applying the formula to solve word problems.\n"
                    f"  Got types: {types}")

            elif current_level == 4 and has_comp:    # L5 — complete-the-formula
                self.assertTrue(c_types,
                    f"{loc}\n"
                    f"  → L5 must include at least one C_-type (complete-the-formula).\n"
                    f"  This card has algebraic symbols that appear in '{card['formula']}'.\n"
                    f"  At L5 the user fills in blanked-out symbols — a NEW challenge.\n"
                    f"  Got types: {types}")

            elif current_level in (5, 6) and has_appqs:  # L6/L7 — hard application
                self.assertTrue(a_types,
                    f"{loc}\n"
                    f"  → {label} must include at least one A-type (hard application, no hint).\n"
                    f"  This card has {len(card['appQs'])} appQ(s). At {label} the user\n"
                    f"  must solve word problems with no formula scaffold.\n"
                    f"  Got types: {types}")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Pass 9 — cross-level distinction
# ─────────────────────────────────────────────────────────────────────────────

def _make_qgen_cross_level_test(card: dict):
    """
    Confirms that the TYPE CATEGORY of questions actually changes across levels.

    For cards with appQs:
      • L1 sessions must NEVER contain A-type or C_-type questions.
      • L6 sessions must NEVER contain R1 (the SVG-aided beginner recognition).

    This is the direct regression test for the bug where L4+ kept showing
    the same L1 recognition questions.
    """
    def test(self):
        cid       = card['id']
        has_appqs = bool(card.get('appQs'))
        # Only meaningful for cards with content diversity
        if not (has_appqs or _count_v_types(card) >= 2):
            return

        l1_runs = _SESSIONS[cid]['0']   # currentLevel=0 → L1
        l6_runs = _SESSIONS[cid]['5']   # currentLevel=5 → L6

        for ri, (s1, s6) in enumerate(zip(l1_runs, l6_runs)):
            if not isinstance(s1, list) or not isinstance(s6, list):
                continue
            t1 = [q.get('type', '') for q in s1]
            t6 = [q.get('type', '') for q in s6]

            if has_appqs and _count_v_types(card) >= 1:
                # Rich card: L1 should be pure recognition — no application or fill-in
                loc1 = _loc(cid, f"L1 run={ri + 1}")
                a_in_l1 = [t for t in t1 if t.startswith('A') and t[1:].isdigit()]
                self.assertFalse(a_in_l1,
                    f"{loc1}\n"
                    f"  → A-type questions MUST NOT appear at L1.\n"
                    f"  Application questions are reserved for L4+.\n"
                    f"  Found: {a_in_l1}  (session: {t1})\n"
                    f"  This indicates the level difficulty is NOT progressing.")

                c_in_l1 = [t for t in t1 if t.startswith('C_')]
                self.assertFalse(c_in_l1,
                    f"{loc1}\n"
                    f"  → C_-type questions MUST NOT appear at L1.\n"
                    f"  Complete-the-formula questions are reserved for L5+.\n"
                    f"  Found: {c_in_l1}  (session: {t1})")

            # L6 is REVERSE SOLVE — R1 (SVG + easy distractors) must never appear
            loc6 = _loc(cid, f"L6 run={ri + 1}")
            r1_in_l6 = [t for t in t6 if t == 'R1']
            self.assertFalse(r1_in_l6,
                f"{loc6}\n"
                f"  → R1 (SVG-aided recognition) MUST NOT appear at L6.\n"
                f"  L6 is 'APPLY HARD' — the user must recall the formula unaided.\n"
                f"  Found: {r1_in_l6}  (session: {t6})\n"
                f"  This indicates L6 is recycling L1-level beginner questions.")
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Sanity
# ─────────────────────────────────────────────────────────────────────────────

class TestSanity(unittest.TestCase):
    """Sanity checks — ensures the data pipeline itself is working."""

    def test_cards_loaded(self):
        self.assertGreaterEqual(len(_CARDS), 30,
            f"Only {len(_CARDS)} cards loaded — expected ≥30. "
            f"Check that FORMULA_CARDS was parsed correctly from {HTML_PATH}.")

    def test_all_card_ids_unique(self):
        ids = [c['id'] for c in _CARDS]
        dupes = [x for x in ids if ids.count(x) > 1]
        self.assertFalse(dupes,
            f"Duplicate card IDs found: {list(set(dupes))}")

    def test_sessions_generated_for_all_cards(self):
        missing = [c['id'] for c in _CARDS if c['id'] not in _SESSIONS]
        self.assertFalse(missing,
            f"No generated sessions for cards: {missing}")

    def test_correct_number_of_levels(self):
        for card in _CARDS:
            cid  = card['id']
            keys = list(_SESSIONS[cid].keys())
            self.assertEqual(len(keys), FL_MASTERY_LEVEL,
                f"[{cid}] expected {FL_MASTERY_LEVEL} level keys, got {len(keys)}: {keys}")

    def test_correct_number_of_runs(self):
        for card in _CARDS:
            cid = card['id']
            for cl in range(FL_MASTERY_LEVEL):
                runs = _SESSIONS[cid][str(cl)]
                self.assertEqual(len(runs), N_RUNS,
                    f"[{cid}] L{cl + 1}: expected {N_RUNS} runs, got {len(runs)}")


# ─────────────────────────────────────────────────────────────────────────────
# Test classes — methods injected dynamically
# ─────────────────────────────────────────────────────────────────────────────

class TestCardStructure(unittest.TestCase):
    """Pass 1 — every FORMULA_CARD has all required fields."""

class TestAppQAnswerCorrectness(unittest.TestCase):
    """Pass 2 — every appQs[i].opts[ans] is in-range and non-empty."""

class TestVarFormat(unittest.TestCase):
    """Pass 3 — every var entry contains an '=' separator."""

class TestQGenStructure(unittest.TestCase):
    """Pass 4 — every generated question has valid fields and ans in range."""

class TestQGenAnswerCorrectness(unittest.TestCase):
    """Pass 5 — opts[ans] matches the semantically correct answer per question type."""

class TestQGenUniqueness(unittest.TestCase):
    """Pass 6 — all FL_SESSION_SIZE type keys within one session are distinct."""

class TestQGenHintPolicy(unittest.TestCase):
    """Pass 7 — formula hint present at L4; absent at L5/L6/L7; no A-types at L1/L2 for rich cards."""

class TestQGenLevelAdaptivity(unittest.TestCase):
    """Pass 8 — each level always surfaces its expected primary question type."""

class TestQGenCrossLevel(unittest.TestCase):
    """Pass 9 — L1 and L6 sessions expose categorically different question types."""


# ── Inject per-card and per-card×level test methods ──────────────────────────
for _card in _CARDS:
    _cid     = re.sub(r'[^a-zA-Z0-9_]', '_', _card['id'])

    # Pass 1 — card structure (one per card)
    setattr(TestCardStructure, f"test_{_cid}",
            _make_card_structure_test(_card))

    # Pass 3 — var format (one per card)
    setattr(TestVarFormat, f"test_{_cid}",
            _make_var_format_test(_card))

    # Pass 9 — cross-level distinction (one per card)
    setattr(TestQGenCrossLevel, f"test_{_cid}",
            _make_qgen_cross_level_test(_card))

    # Pass 2 — one per appQ entry
    for _qi, _appq in enumerate(_card.get('appQs', [])):
        setattr(TestAppQAnswerCorrectness, f"test_{_cid}_appq{_qi}",
                _make_appq_test(_card, _qi, _appq))

    # Passes 4–8 — one per card × level
    for _cl in range(FL_MASTERY_LEVEL):
        _suffix = f"{_cid}_L{_cl + 1}"
        setattr(TestQGenStructure,        f"test_{_suffix}",
                _make_qgen_structure_test(_card, _cl))
        setattr(TestQGenAnswerCorrectness, f"test_{_suffix}",
                _make_qgen_answer_test(_card, _cl))
        setattr(TestQGenUniqueness,        f"test_{_suffix}",
                _make_qgen_uniqueness_test(_card, _cl))
        setattr(TestQGenHintPolicy,        f"test_{_suffix}",
                _make_qgen_hint_policy_test(_card, _cl))
        setattr(TestQGenLevelAdaptivity,   f"test_{_suffix}",
                _make_qgen_adaptivity_test(_card, _cl))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    n_cards  = len(_CARDS)
    n_appqs  = sum(len(c.get('appQs', [])) for c in _CARDS)
    n_qs_gen = n_cards * FL_MASTERY_LEVEL * N_RUNS * FL_SESSION_SIZE
    n_tests  = (
        5                                    # TestSanity
        + n_cards                            # Pass 1 structure
        + n_appqs                            # Pass 2 appQ correctness
        + n_cards                            # Pass 3 var format
        + n_cards * FL_MASTERY_LEVEL * 5     # Passes 4–8 (5 suites per card×level)
        + n_cards                            # Pass 9 cross-level
    )
    print(f"\n{'='*62}")
    print(f"  ASVAB SIM — Formula Lab Tests")
    print(f"{'='*62}")
    print(f"  Cards loaded       : {n_cards}")
    print(f"  appQs total        : {n_appqs}")
    print(f"  Runs per card×level: {N_RUNS}")
    print(f"  Questions generated: {n_qs_gen:,}")
    print(f"  Test cases total   : ~{n_tests:,}")
    print(f"{'='*62}\n")
    unittest.main(verbosity=2)
