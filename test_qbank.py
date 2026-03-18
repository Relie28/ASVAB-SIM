#!/usr/bin/env python3
"""
ASVAB SIM — Question Bank Unit Tests
======================================
Runs against /Users/aurelienessome/Desktop/ASVAB SIM/index.html.

Test suites
-----------
  TestStructure            — every question has required fields, ans is in range
  TestCodeTagMatchesAnswer — last <code> in exp exactly matches opts[ans]
  TestArithmetic           — every A×B=C, A÷B=C, A+B=C in explanations is correct
  TestPercentageMultiplier — every (−X%) pattern uses the right multiplier ×(1−X/100)
  TestDuplicates           — duplicate question texts always share the same correct answer

Usage
-----
  python3 test_qbank.py              # brief summary
  python3 test_qbank.py -v           # verbose per-test output
  python3 test_qbank.py -v 2>&1 | grep -E "FAIL|ERROR|OK"  # summary line only
"""

import re
import math
import unittest

HTML_PATH   = '/Users/aurelienessome/Desktop/ASVAB SIM/index.html'
UNICODE_MINUS = '\u2212'   # −  (U+2212 MINUS SIGN, used in HTML math)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def strip_html(html: str) -> str:
    """Remove all HTML tags and decode common entities."""
    s = re.sub(r'<[^>]+>', ' ', html)
    s = (s.replace('&amp;', '&').replace('&lt;', '<')
          .replace('&gt;', '>').replace('&nbsp;', ' '))
    return re.sub(r'\s+', ' ', s).strip()


def normalize(s: str) -> str:
    """
    Canonical form used for answer-text comparison.
    Strips HTML, unifies Unicode minus → ASCII minus, removes $, commas,
    whitespace; lowercases.
    """
    s = strip_html(str(s))
    s = s.replace(UNICODE_MINUS, '-')   # − → -
    s = re.sub(r'[$,\s]', '', s)
    return s.lower()


def parse_number(s: str) -> float:
    """Parse a numeric string that may contain $, commas, Unicode minus."""
    s = str(s).replace(UNICODE_MINUS, '-').replace('$', '').replace(',', '')
    try:
        return float(s)
    except ValueError:
        return float('nan')


# ─────────────────────────────────────────────────────────────────────────────
# Question bank loader
# ─────────────────────────────────────────────────────────────────────────────

def load_questions():
    """Parse every question object from PICAT_QUESTIONS in index.html.

    Handles all section formats:
      • MK / AR  — forced:"...",  q:...
      • WK       — forced:"...", initiallyWrong:true,  q:...
      • PC       — forced:"...", passage:"...",         q:...
      • GS / EI / AI / MC / AO — no forced, no passage, q:...
    """
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    STR   = r'"(?:[^"\\]|\\.)*"'     # any double-quoted string (with escapes)
    BOOL  = r'(?:true|false)'
    NULL  = r'null'

    pattern = (
        r'\{section:"([^"]+)",diff:(\d+),'
        # optional: forced:null  or  forced:"..."
        r'(?:forced:(?:' + NULL + r'|' + STR + r'),)?'
        # optional: initiallyWrong:true/false
        r'(?:initiallyWrong:' + BOOL + r',)?'
        # optional: passage:"..."  BEFORE q  (PC format)
        r'(?:passage:' + STR + r',)?'
        # required: q:"..."
        r'q:"((?:[^"\\]|\\.)*)"'
        # optional: passage:"..."  AFTER q  (legacy/alternate format)
        r'(?:,passage:' + STR + r')?'
        # required: opts / ans / exp
        r'\s*,opts:\[(.*?)\]'
        r'\s*,ans:(\d+)'
        r',exp:"((?:[^"\\]|\\.)*)"'
    )
    questions = []
    for m in re.finditer(pattern, content, re.DOTALL):
        section, diff, q, opts_raw, ans_str, exp = m.groups()
        opts = re.findall(r'"((?:[^"\\]|\\.)*)"', opts_raw)
        questions.append({
            'section': section,
            'diff':    int(diff),
            'q':       q,
            'opts':    opts,
            'ans':     int(ans_str),
            'exp':     exp,
        })
    if not questions:
        raise RuntimeError(f"No questions parsed from {HTML_PATH} — check the regex.")
    return questions


QUESTIONS = load_questions()

# ─────────────────────────────────────────────────────────────────────────────
# Test-case factories
# ─────────────────────────────────────────────────────────────────────────────

def _loc(i, q):
    return f"Q[{i:03d}] {q['section']} diff={q['diff']}: \"{q['q'][:70]}\""


def _make_structure_test(q, i):
    """Pass 1 — required fields, ans in range."""
    def test(self):
        loc = _loc(i, q)
        self.assertTrue(q['q'].strip(),
            f"{loc}\n  → question text is empty")
        self.assertIn('section', q,
            f"{loc}\n  → missing 'section' field")
        self.assertTrue(q['section'].strip(),
            f"{loc}\n  → section is empty")
        self.assertIsInstance(q['ans'], int,
            f"{loc}\n  → 'ans' must be an integer, got {type(q['ans'])}")
        self.assertGreaterEqual(q['ans'], 0,
            f"{loc}\n  → ans={q['ans']} is negative")
        self.assertGreaterEqual(len(q['opts']), 2,
            f"{loc}\n  → needs at least 2 options, got {len(q['opts'])}")
        self.assertLess(q['ans'], len(q['opts']),
            f"{loc}\n  → ans={q['ans']} out of range "
            f"(opts has {len(q['opts'])} items, valid range 0–{len(q['opts'])-1})")
        self.assertTrue(q['opts'][q['ans']].strip(),
            f"{loc}\n  → opts[ans={q['ans']}] is empty")
        self.assertTrue(q['exp'].strip(),
            f"{loc}\n  → explanation (exp) is empty")
    return test


def _make_code_tag_test(q, i):
    """
    Pass 2 — the final <code>…</code> in exp must exactly match opts[ans].

    Both sides are normalized (HTML stripped, Unicode minus → ASCII minus,
    $, commas, whitespace removed, lowercased) before comparison.
    The test FAILS if the normalized strings are not equal.
    """
    def test(self):
        exp = q['exp']
        code_tags = re.findall(r'<code>(.*?)</code>', exp, re.IGNORECASE)
        if not code_tags:
            return  # no code tag present — nothing to check

        last_code   = code_tags[-1].strip()
        correct_opt = q['opts'][q['ans']].strip()
        nc = normalize(last_code)
        no = normalize(correct_opt)

        if len(nc) < 2 or len(no) < 2:
            return  # too short to compare meaningfully

        loc = _loc(i, q)
        self.assertEqual(nc, no,
            f"{loc}\n"
            f"  explanation ends with : <code>{last_code}</code>\n"
            f"  correct option is     : \"{correct_opt}\"\n"
            f"  normalized code tag   : '{nc}'\n"
            f"  normalized option     : '{no}'\n"
            f"  → The explanation points to a DIFFERENT answer than opts[ans={q['ans']}].")
    return test


def _make_arithmetic_test(q, i):
    """
    Pass 3 — every arithmetic expression in the explanation must be correct.

    Checks:
      • A × B = C   (Unicode × only, so variable 'x' is never matched)
      • A ÷ B = C
      • $A + $B = $C  (dollar-anchored to avoid false positives)
      • $A − $B = $C  (dollar-anchored)
    Tolerance: max($1, 0.2% of the stated value) to allow normal rounding.
    """
    def test(self):
        # Work in plain text with ASCII minus so regexes are uniform
        plain = strip_html(q['exp']).replace(UNICODE_MINUS, '-')
        loc   = _loc(i, q)
        errors = []

        tol_fn = lambda stated: max(1.0, abs(stated) * 0.002)

        # ── A × B = C  (× U+00D7 only — never matches variable 'x') ──
        # Skip if this is a multi-term chain: A × B × C = D — in that case the
        # regex matches the last two factors (B × C = D) which gives a false
        # positive because B × C ≠ D (only A × B × C = D is true).  Detect by
        # checking whether the character immediately before the match (after
        # stripping whitespace) is itself a '×' sign.
        for m in re.finditer(
                r'\$?([\d,]+\.?\d*)\s*\xd7\s*([\d,]+\.?\d*)\s*=\s*\$?([\d,]+\.?\d*)(?![a-zA-Z0-9])',
                plain):
            pre = plain[:m.start()].rstrip()
            if pre and pre[-1] == '\xd7':   # preceded by another × → chain, skip
                continue
            a, b, stated = parse_number(m[1]), parse_number(m[2]), parse_number(m[3])
            if any(math.isnan(v) for v in (a, b, stated)) or stated == 0:
                continue
            computed = round(a * b, 2)
            if abs(computed - stated) > tol_fn(stated):
                errors.append(f"  multiplication: {a} × {b} = {stated}  (computed {computed})")

        # ── A ÷ B = C ──
        for m in re.finditer(
                r'\$?([\d,]+\.?\d*)\s*\xf7\s*([\d,]+\.?\d*)\s*=\s*\$?([\d,]+\.?\d*)',
                plain):
            a, b, stated = parse_number(m[1]), parse_number(m[2]), parse_number(m[3])
            if any(math.isnan(v) for v in (a, b, stated)) or b == 0 or stated == 0:
                continue
            computed = round(a / b, 2)
            if abs(computed - stated) > tol_fn(stated):
                errors.append(f"  division: {a} ÷ {b} = {stated}  (computed {computed})")

        # ── $A + $B = $C  (dollar-anchored to avoid algebraic false positives) ──
        for m in re.finditer(
                r'\$([\d,]+\.?\d*)\s*\+\s*\$([\d,]+\.?\d*)\s*=\s*\$([\d,]+\.?\d*)',
                plain):
            a, b, stated = parse_number(m[1]), parse_number(m[2]), parse_number(m[3])
            if any(math.isnan(v) for v in (a, b, stated)):
                continue
            computed = round(a + b, 2)
            if abs(computed - stated) > tol_fn(stated):
                errors.append(f"  addition: ${a} + ${b} = ${stated}  (computed {computed})")

        # ── $A - $B = $C  (dollar-anchored subtraction) ──
        for m in re.finditer(
                r'\$([\d,]+\.?\d*)\s*-\s*\$([\d,]+\.?\d*)\s*=\s*\$([\d,]+\.?\d*)',
                plain):
            a, b, stated = parse_number(m[1]), parse_number(m[2]), parse_number(m[3])
            if any(math.isnan(v) for v in (a, b, stated)):
                continue
            computed = round(a - b, 2)
            if abs(computed - stated) > tol_fn(stated):
                errors.append(f"  subtraction: ${a} - ${b} = ${stated}  (computed {computed})")

        if errors:
            self.fail(f"{loc} — arithmetic error(s) in explanation:\n" + "\n".join(errors))
    return test


def _make_percentage_test(q, i):
    """
    Pass 4 — every '(−X%)' label in an explanation must pair with ×(1−X/100).

    Example: '(−15%): $24,000 × 0.85' is valid.
             '(−5%):  $18,360 × 0.95' is also valid.
             '(−10%): $18,360 × 0.95' is INVALID (should be 0.90).
    Tolerance: ±0.005 to allow for displayed rounding.
    """
    def test(self):
        plain = strip_html(q['exp']).replace(UNICODE_MINUS, '-')
        loc   = _loc(i, q)
        errors = []

        # Match '(-X%): ...' followed closely by '× 0.YY'
        for m in re.finditer(
                r'\(-(\d+(?:\.\d+)?)%\)[^×\xd7]*[×\xd7]\s*(0\.\d+)',
                plain):
            pct      = float(m[1])
            mult     = float(m[2])
            expected = round(1.0 - pct / 100.0, 4)
            if abs(mult - expected) > 0.005:
                errors.append(
                    f"  (-{pct}%) should use multiplier ×{expected:.3f} "
                    f"but explanation has ×{mult}")

        if errors:
            self.fail(
                f"{loc} — percentage / multiplier mismatch(es) in explanation:\n"
                + "\n".join(errors))
    return test


# ─────────────────────────────────────────────────────────────────────────────
# Test classes — methods injected dynamically so every question is its own test
# ─────────────────────────────────────────────────────────────────────────────

class TestStructure(unittest.TestCase):
    """Pass 1 — all required fields present; ans index is valid."""


class TestCodeTagMatchesAnswer(unittest.TestCase):
    """Pass 2 — explanation <code> tag matches opts[ans] exactly (normalized)."""


class TestArithmetic(unittest.TestCase):
    """Pass 3 — all arithmetic expressions (×, ÷, $+, $−) are numerically correct."""


class TestPercentageMultiplier(unittest.TestCase):
    """Pass 4 — every (−X%) label pairs with the correct multiplier ×(1−X/100)."""


for _i, _q in enumerate(QUESTIONS):
    _suffix = f"{_i:03d}"
    setattr(TestStructure,           f"test_{_suffix}", _make_structure_test(_q, _i))
    setattr(TestCodeTagMatchesAnswer, f"test_{_suffix}", _make_code_tag_test(_q, _i))
    setattr(TestArithmetic,           f"test_{_suffix}", _make_arithmetic_test(_q, _i))
    setattr(TestPercentageMultiplier, f"test_{_suffix}", _make_percentage_test(_q, _i))


# ─────────────────────────────────────────────────────────────────────────────
# Pass 5 — Duplicate question integrity (single class-level test)
# ─────────────────────────────────────────────────────────────────────────────

class TestDuplicates(unittest.TestCase):
    """
    Pass 5 — any question text that appears more than once must always point
    to the same correct answer (by normalized option text).
    """

    def test_no_conflicting_duplicates(self):
        """
        Two entries with identical question text AND overlapping option sets must
        agree on which answer text is correct.

        Entries with the same question text but completely disjoint option sets
        are different question variants (same stem, different choices) and are
        NOT considered conflicting duplicates — they are flagged separately as
        informational warnings in the console.
        """
        canonical = {}   # norm_question_text → {'idx': int, 'correct': str, 'raw': str, 'opts_n': set}
        conflicts = []
        variant_pairs = []  # same text, disjoint opts — informational only

        for i, q in enumerate(QUESTIONS):
            norm_q      = normalize(q['q'])
            correct_raw = q['opts'][q['ans']]
            correct_n   = normalize(correct_raw)
            opts_n      = set(normalize(o) for o in q['opts'])

            if norm_q not in canonical:
                canonical[norm_q] = {'idx': i, 'correct': correct_n, 'raw': correct_raw, 'opts_n': opts_n}
            else:
                prev = canonical[norm_q]
                # Two questions conflict only when their correct answers exist in the
                # same answer universe.  Specifically: if q1's correct answer
                # appears in q2's option list (or vice versa), they share an
                # answer space and must agree.  If NEITHER correct answer crosses
                # over, they are different variants of the same stem (different
                # option sets, different answer keys) — not a true conflict.
                correct_in_prev = correct_n in prev['opts_n']
                prev_correct_in_curr = prev['correct'] in opts_n

                if not correct_in_prev and not prev_correct_in_curr:
                    # Neither correct answer appears in the other's option set →
                    # different question variants, not a true duplicate conflict.
                    variant_pairs.append(
                        f"  Q[{i:03d}] vs Q[{prev['idx']:03d}]: same stem, different answer spaces "
                        f"(correct \"{q['opts'][q['ans']]}\" vs \"{QUESTIONS[prev['idx']]['opts'][QUESTIONS[prev['idx']]['ans']]}\")"
                    )
                elif prev['correct'] != correct_n:
                    # Same (or overlapping) options but different answer → genuine conflict.
                    conflicts.append(
                        f"  Q[{i:03d}] vs Q[{prev['idx']:03d}]:\n"
                        f"    Q[{i:03d}] correct: \"{correct_raw}\"\n"
                        f"    Q[{prev['idx']:03d}] correct: \"{prev['raw']}\"\n"
                        f"    question: \"{q['q'][:80]}\""
                    )

        if variant_pairs:
            print(f"\n  [INFO] {len(variant_pairs)} same-stem variant pair(s) with disjoint options "
                  f"(not conflicts):\n" + "\n".join(variant_pairs))

        if conflicts:
            self.fail(
                f"{len(conflicts)} duplicate question(s) with conflicting answer keys:\n"
                + "\n".join(conflicts))

    def test_question_count_not_zero(self):
        """Sanity check: ensure the HTML parser found questions at all."""
        self.assertGreater(len(QUESTIONS), 100,
            f"Only {len(QUESTIONS)} questions parsed — check the regex in load_questions().")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Print a header so the output is easy to read
    total = len(QUESTIONS)
    sections = {}
    for q in QUESTIONS:
        sections[q['section']] = sections.get(q['section'], 0) + 1
    sec_summary = ', '.join(f"{s}:{n}" for s, n in sorted(sections.items()))
    print(f"\n{'='*60}")
    print(f"ASVAB SIM Question Bank Tests")
    print(f"Questions loaded: {total}  ({sec_summary})")
    print(f"Test cases: {total * 4 + 2}  "
          f"(structure + code-tag + arithmetic + pct/multiplier × {total}, "
          f"+ 2 duplicate tests)")
    print(f"{'='*60}\n")
    unittest.main(verbosity=2)
