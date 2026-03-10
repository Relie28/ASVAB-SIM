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

### Full ASVAB

Calculates a **standard score** (20–80 scale), **VE (Verbal Expression)** from WK + PC, and a **composite AFQT score** with percentile ranking.

```
VE  = (WK% + PC%) / 2  → converted to standard score
AFQT composite = 2×VE + AR_std + MK_std
```

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
