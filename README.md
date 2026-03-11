# ASVAB SIM — PICAT Verification Prep

**🔗 Live app → [https://relie28.github.io/ASVAB-SIM/](https://relie28.github.io/ASVAB-SIM/)**

A single-file, offline-capable web app built to simulate and reinforce performance on the **ASVAB / PICAT** (Pre-screening, Internet-delivered Computerized Adaptive Test). Built specifically around one user's real test results to drill the exact questions they missed, prepare for PICAT verification, and target an **AFQT score at the 95th percentile**.

---

## What It Is

When you take the PICAT, your answers are saved. If you score high enough to qualify for enlistment, you are later given a **Verification Test** — a shorter, proctored version of the ASVAB that confirms your PICAT score was genuine. If your Verification score doesn't match your PICAT within a margin, your PICAT score is discarded.

This app exists to close that gap. It reconstructs your real PICAT session — every question you answered, every section score — and turns it into a repeatable, adaptive drill tool so you can walk into the Verification Test knowing the material cold.

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

The AFQT is not a raw percentage. It's a **percentile rank** derived from a six-step pipeline that weights difficulty, normalizes scores, and compares you to a national reference population.

---

#### Step 1 — Raw Correct Answers

You start with accuracy per section. Using the scores this app is built around as an example:

| Section | Correct | Accuracy |
| ------- | ------- | -------- |
| AR      | 13/15   | 87%      |
| WK      | 11/15   | 73%      |
| PC      | 8/10    | 80%      |
| MK      | 11/15   | 73%      |

But two people with 11/15 can receive **different scaled scores** depending on which 11 they got right — because each question carries a difficulty weight.

---

#### Step 2 — Item Response Theory (Difficulty Weighting)

The PICAT uses adaptive-style scoring. Each question has three parameters:

- **Difficulty** — how hard the question is
- **Discrimination** — how well it separates high vs. low ability test-takers
- **Guess probability** — the likelihood of getting it right by chance

These are combined to estimate your **ability level (θ, "theta")** per section — a continuous measure of true ability, not a raw count.

Conceptually, the ability estimates for the above scores might look like:

```
θ_AR ≈ 0.90   (very strong)
θ_PC ≈ 0.70   (strong)
θ_MK ≈ 0.80   (solid)
θ_WK ≈ 0.50   (moderate)
```

---

#### Step 3 — Standard Scores (20–80 scale)

Each theta estimate is converted to a **standard score** on a 20–80 scale. This scale is normalized so that:

- **50** = population average
- **60** ≈ top 16%
- **70** ≈ top 2%

Approximate standard scores for the example above:

| Section | Estimated Standard Score |
| ------- | ------------------------ |
| AR      | ~65–70                   |
| MK      | ~60–65                   |
| PC      | ~60–65                   |
| WK      | ~55–60                   |

---

#### Step 4 — Build VE (Verbal Expression)

VE is a composite of WK and PC.

```
VE_raw = WK_standard + PC_standard
       = 58 + 63 = 121
```

That raw sum is run through a **DoD lookup table** to produce a final VE standard score:

```
VE ≈ 62
```

---

#### Step 5 — AFQT Composite

The AFQT composite is calculated as:

```
AFQT = 2 × VE + AR + MK
```

Using the example values:

```
AFQT = 2(62) + 67 + 63
     = 124 + 130
     = 254
```

> **Note:** VE is doubled. This means Verbal (WK + PC) counts for **half** of your total AFQT. Improving your vocabulary by 2–3 questions has a disproportionately large effect on the final score.

---

#### Step 6 — Convert Composite → Percentile

That composite is compared against a norming sample of thousands of Americans to produce your final **percentile rank**:

| Composite | Approximate Percentile |
| --------- | ---------------------- |
| 235       | ~90th                  |
| 245       | ~93rd                  |
| 255       | ~95th                  |
| 265       | ~97th                  |

A composite of ~254 → **AFQT 95** — meaning you scored higher than 95% of the reference population.

---

#### What the Scores Actually Say

| Section | Takeaway |
| ------- | -------- |
| AR      | Extremely strong — your math **carried** the test |
| PC      | Strong |
| MK      | Solid |
| WK      | Moderate — the biggest lever for improvement |

Because VE (WK + PC) is **doubled** in the formula, 2–3 more correct vocabulary answers could push the AFQT from 95 to **97–99**.

---

#### What a 95 Means for Enlistment

- Anything above 93 is effectively the **same qualification tier**
- You already qualify for nearly every enlisted MOS/rating
- At this point, **line scores** (GT, ST, EL, etc.) matter more to your recruiter than the AFQT percentile

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
4. Tap **FULL ASVAB SIMULATION** for a full-length practice test
5. Tap **VIEW MY STATS** to see your history across sessions

---

## Technical Notes

- **Single file** — all HTML, CSS, and JavaScript in `index.html` (~1,900 lines)
- **No dependencies** — no build step, no npm, no frameworks
- **Fonts** — loaded from Google Fonts (Barlow Condensed, IBM Plex Mono); app is functional without them
- **Persistence** — session stats stored in `localStorage` under the key `asvab_stats` (up to 50 sessions retained)
- **Responsive** — media queries at 768 px, 600 px, and 400 px for tablet and mobile

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
