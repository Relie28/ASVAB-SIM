# ASVAB SIM — AFQT 95 ✓

**🔗 Live app → [https://relie28.github.io/ASVAB-SIM/](https://relie28.github.io/ASVAB-SIM/)**

A single-file, offline-capable web app built to simulate and reinforce performance on the **ASVAB / PICAT** (Pre-screening, Internet-delivered Computerized Adaptive Test). Built around one user's real verified test results — **official AFQT 95 confirmed, March 2026** — and kept live as an ongoing drill tool for continued prep and score maintenance.

> **Official scores (CAT-ASVAB · March 2026)**
> | Section | Correct | Standard Score |
> |---------|---------|---------------|
> | AR | 13 / 16 | 65 |
> | WK | 11 / 16 | 60 |
> | PC | 9 / 11 | 68 |
> | MK | 12 / 16 | 62 |
> | GS | 9 / 16 | 51 |
>
> **AFQT: 95**

---

## What It Is

When you take the PICAT, your answers are saved. If you score high enough to qualify for enlistment, you are later given a **Verification Test** — a shorter, proctored version of the ASVAB that confirms your PICAT score was genuine. If your Verification score doesn't match your PICAT within a margin, your PICAT score is discarded.

This app was built to close that gap. It reconstructs the real PICAT session — every question, every section score — and turns it into a repeatable, adaptive drill tool. The target was AFQT 95. **That target has been met and confirmed.**

The app remains live as a maintenance and improvement tool across all AFQT subtests.

---

## Modes

### PICAT Verification Drill (30 questions · 25 minutes)

The primary mode. Pulls from a curated bank of **130 real-test and practice questions** across four AFQT sections:

| Section | Full Name               | Questions in pool |
| ------- | ----------------------- | ----------------- |
| AR      | Arithmetic Reasoning    | 38                |
| WK      | Word Knowledge          | 26                |
| PC      | Paragraph Comprehension | 21                |
| MK      | Mathematics Knowledge   | 45                |

Every session is intelligently assembled using **weighted sampling**:

- Questions you **missed on the real PICAT** → always included (guaranteed)
- Questions you got **right on the real PICAT** → high weight (rehearse your hits)
- Harder fresh questions → medium weight
- Easier fresh questions → lower weight

Questions and answer options are **shuffled on every session** so you can't memorize position.

### Full ASVAB Simulation (71 questions · 90 minutes)

A complete ASVAB simulation in real test order: **GS → AR → WK → PC → MK**. Draws from a pool of **118 original questions** — only 71 are selected per session, so the question mix changes every time. AFQT score is calculated from AR + WK + PC + MK.

---

## Difficulty Flavors

Every session (both modes) is randomly assigned one of three difficulty profiles:

| Flavor          | Effect                                   |
| --------------- | ---------------------------------------- |
| **BALANCED**    | Equal weight across easy / medium / hard |
| **CHALLENGING** | Strongly favors hard questions           |
| **REVIEW**      | Strongly favors easy questions           |

The active flavor is shown as a small badge in the quiz header. This ensures that even if you see a repeated question, the surrounding session context — and the difficulty pressure — varies.

---

## Adaptive Engine (PICAT mode)

Within the PICAT drill, the order of questions adapts live as you answer:

- Answer **2 consecutive questions correctly** in the same section → the next hard question for that section is promoted to appear immediately, escalating the challenge
- Miss a question → streak resets, pressure eases

---

## Real-Test Question Behavior

Questions pulled directly from your real PICAT carry special behavior:

- A **REAL Q** badge (green) or **REAL MISS** badge (red) identifies them
- When you answer a REAL Q, the app shows **exactly what you selected on the real test** (highlighted in gold), letting you compare your original response to your current one
- If you **matched your original wrong answer**, the correct answer is intentionally withheld — so you're forced to reason it out again next time, not just memorize the reveal

---

## Scoring

### PICAT Drill

Reports per-section accuracy and a raw score percentage at the end.

### Full ASVAB — How the AFQT Is Actually Calculated

The AFQT is not a raw percentage. It's a **percentile rank** derived from a pipeline that normalizes per-section accuracy into standard scores, combines them into a composite, and maps that composite onto a national reference population.

---

#### Step 1 — Raw Correct Answers

Accuracy is computed per section. The verified real-test scores this app is anchored to:

| Section | Correct | Accuracy | Standard Score |
| ------- | ------- | -------- | -------------- |
| AR      | 13 / 16 | 81.25%   | 65             |
| WK      | 11 / 16 | 68.75%   | 60             |
| PC      | 9 / 11  | 81.8%    | 68             |
| MK      | 12 / 16 | 75.0%    | 62             |

---

#### Step 2 — Item Response Theory (Difficulty Weighting)

The PICAT uses adaptive-style scoring. Each question has three parameters:

- **Difficulty** — how hard the question is
- **Discrimination** — how well it separates high vs. low ability test-takers
- **Guess probability** — the likelihood of getting it right by chance

These are combined to estimate your **ability level (θ, "theta")** per section — a continuous measure of true ability, not a raw count.

**How this app approximates it:**

Every question in the bank has a `diff` field (`1` easy, `2` medium, `3` hard). The `diff` value drives two things:

1. **Session flavor sampling** — CHALLENGING sessions draw proportionally more hard questions; REVIEW sessions draw more easy ones.
2. **Result badges** — correct/incorrect hard questions are highlighted in the question review.

For the standard score calculation itself, raw accuracy (`correct / total`) is used with calibrated per-section slopes. Applying bonus weights for hard questions creates a systematic downward bias — realistic test-takers concentrate misses on harder items — so difficulty weights are excluded from scoring.

---

#### Step 3 — Standard Scores (20–80 scale)

Raw accuracy per section is converted to a **standard score** on a 20–80 scale using per-section slopes calibrated directly from the verified real-test data:

```
std = 50 + (pct − 0.5) × slope
```

| Section | Slope | Derivation |
| ------- | ----- | ---------- |
| AR      | 48    | 13/16 (81.25%) → SS 65 |
| WK      | 53    | 11/16 (68.75%) → SS 60 |
| PC      | 57    | 9/11  (81.8%)  → SS 68 |
| MK      | 48    | 12/16 (75.0%)  → SS 62 |

Each slope is solved algebraically from the real score: `slope = (SS − 50) / (accuracy − 0.5)`. PC uses a steeper slope because fewer questions (11 vs. 16) means each carries more weight on the real test.

---

#### Step 4 — Build VE (Verbal Expression)

VE is derived from **combined WK+PC raw performance** — mirroring how the real ASVAB computes it from the sum of correct WK and PC answers before any scaling:

```
VE_pct = (WK_correct + PC_correct) / (WK_total + PC_total)
VE_std  = 50 + (VE_pct − 0.5) × 58
```

Using the real test: (11 + 9) / (16 + 11) = 0.741 → **VE = 64**

The slope `58` is calibrated so that this combined-raw approach reproduces the verified composite:

```
VE = 64   →   2×VE = 128   →   128 + 65 + 62 = 255   →   AFQT 95 ✓
```

> **Why not just average the two standard scores?**  
> Averaging `(WK_std + PC_std) / 2` treats WK's 16 questions and PC's 11 questions as equally weighted. On the real ASVAB, VE is derived from the combined raw sum — so a miss on PC hurts more than a miss on WK. The combined-raw method captures this correctly.

---

#### Step 5 — AFQT Composite

```
AFQT = 2 × VE + AR + MK
     = 2(64) + 65 + 62
     = 128 + 65 + 62
     = 255
```

> **VE is doubled.** Verbal (WK + PC) accounts for **half** of your total AFQT. Improving by 2–3 vocabulary questions has a disproportionately large effect on your final score.

---

#### Step 6 — Convert Composite → Percentile

The composite is mapped to a percentile using a **normal distribution** approximation of the DoD 1997 norming sample:

```
Percentile = Φ((composite − 200) / 33.4) × 100
```

- **Mean = 200** — corresponds to 50th percentile (all sections at standard score 50)  
- **SD = 33.4** — derived so that composite 255 maps to exactly the 95th percentile

$$\Phi\!\left(\frac{255-200}{33.4}\right) = \Phi(1.647) \approx 95.0\%\ ✓$$

Cross-checks against known data points:

| Composite | Calculated | Expected |
| --------- | ---------- | -------- |
| 200       | 50th       | ~50th ✓  |
| 235       | ~83rd      | ~80th ✓  |
| 245       | ~90th      | ~90th ✓  |
| 255       | **95th**   | **95th ✓** |
| 265       | ~98th      | ~98th ✓  |
| 270       | ~98.5th    | ~99th ✓  |

This replaces the previous hand-crafted lookup table with a smooth, continuous, mathematically grounded function.

---

#### What a 95 Means for Enlistment

- Anything above 93 is effectively the **same qualification tier**
- Qualifies for nearly every enlisted MOS/rating across all branches
- At this level, **line scores** (GT, ST, EL, etc.) matter more to your recruiter than the AFQT percentile
- **This score has been officially confirmed** — the app continues to serve as a maintenance and improvement tool

---

## Screens

| Screen              | Purpose                                                                                            |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| **Home (Splash)**   | Shows your real PICAT section scores, launches either mode                                         |
| **Category Select** | Toggle which AFQT sections to include in the drill; allocation scales proportionally               |
| **Quiz**            | Active question — section tag, difficulty badge, adaptive timer, progress bar                      |
| **Results**         | Full breakdown by section with question-by-question review                                         |
| **Stats Dashboard** | Tracks session history in `localStorage` — AFQT trend, per-section accuracy bars, last 50 sessions |

---

## How to Use

1. Open `index.html` in any modern browser (Chrome, Safari, Firefox, Edge)
2. No server required — runs entirely offline
3. Tap **BEGIN TIMED QUIZ** for the adaptive PICAT drill
4. Tap **ASVAB SIMULATION** for a full-length practice test
5. Tap **VIEW MY STATS** to see your history across sessions

---

## Technical Notes

- **Single file** — all HTML, CSS, and JavaScript in `index.html` (~6,200 lines)
- **No dependencies** — no build step, no npm, no frameworks
- **Fonts** — loaded from Google Fonts (Barlow Condensed, IBM Plex Mono); app is functional without them
- **Persistence** — session stats stored in `localStorage` under the key `asvab_stats` (up to 50 sessions retained)
- **Responsive** — media queries at 768 px, 600 px, and 400 px for tablet and mobile
- **Scoring engine** — per-section slopes (AR 48 · WK 53 · PC 57 · MK 48) + combined-raw VE (slope 58) + normal CDF percentile (μ=200, σ=33.4); all calibrated to verified AFQT 95 anchor
- **Integrity audits** — `auditQuestionBank()` and `auditExplanations()` run on page load and auto-patch conflicting answer keys; `auditUserAnswers()` runs before scoring to recover any points lost to stale answer-key bugs

---

## File Structure

```
ASVAB SIM/
└── index.html     ← entire app (questions, logic, UI, styles)
└── README.md      ← this file
```

---

## Question Bank Summary

| Bank              | Sections           | Total questions | Used per session     |
| ----------------- | ------------------ | --------------- | -------------------- |
| `PICAT_QUESTIONS` | AR, WK, PC, MK     | 130             | up to 30 (weighted)  |
| `FULL_QB`         | GS, AR, WK, PC, MK | 118             | 71 (flavor-weighted) |

Questions in `PICAT_QUESTIONS` carry metadata:

- `forced` — the exact text of the answer you selected on the real PICAT (or `null` for fresh questions)
- `initiallyWrong: true` — you missed this question on the real test
- `diff` — difficulty tier: `1` easy · `2` medium · `3` hard
