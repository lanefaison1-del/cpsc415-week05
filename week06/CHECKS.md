# Week 6 checks

All runs on November 2, 2026, Python 3.11 in `.venv`, `openrouter` 1.3.106, from `week06/`.

## The test loop, red then green
| Step | Before the code | After the code |
|---|---|---|
| Checker (`tests/test_critic_checker.py`) | collection error: no `critique` module | 39 passed, 25 skipped (Week 5's model tests) |
| Generator (`tests/test_generate.py`) | collection error: no `generate` module | 46 passed, 25 skipped |

No test calls a model; the billed runs below are commands, run once each.

## Guard
The lab says the guard should refuse `pip install openrouter` until `spec.md` names it. Mine let it
through (exit 0): the guard looks for the package name anywhere in the lowercased spec, and my
Week 5 spec already says "OpenRouter" and `OPENROUTER_API_KEY`. The spec now names `openrouter`
under Dependencies anyway, before it was installed.

## Five images, FLUX.2 klein (`images/`)
| Image | Seed | Cost | Seconds | What I saw | MiniMax checklist | MiniMax name read | MiMo checklist | MiMo name read |
|---|---|---|---|---|---|---|---|---|
| fernkit | 6301 | $0.014 | 4.9 | all 6 met, name correct | ok | FERNKIT (match) | ok | FERNKIT (match) |
| dunekit | 6302 | $0.014 | 3.8 | all 6 met, name correct | ok | DUNEKIT (match) | ok | DUNEKIT (match) |
| reefkit | 6303 | $0.014 | 3.7 | all 6 met, name correct | ok | **REFKIT (MISMATCH)** | **2 unmet**: banner, no other text | **REFKIT (MISMATCH)** |
| citykit | 6304 | $0.014 | 3.2 | all 6 met, name correct | ok | CITYKIT (match) | ok | CITYKIT (match) |
| snowkit | 6305 | $0.014 | 3.6 | all 6 met, name correct | ok | SNOWKIT (match) | ok | SNOWKIT (match) |

Generation $0.0700. Critiques (checklist plus name read per image): MiniMax $0.00338, MiMo $0.00060.
I looked at all five before reading any critique. By my eye every image meets all six
requirements and every banner is spelled right, so the code's two REEFKIT flags are the critics'
misreads, not a misspelled image.

**A run that happened twice.** The first critique command was started over a connection that
timed out; the command kept running while I started it again, so both critics ran twice (about
$0.004 extra) and the two runs wrote the same files. The files committed are the last complete
run of each. The runs did not agree with each other: one MiniMax run reported one FERNKIT
requirement unmet, and one MiMo run reported a CITYKIT requirement unmet. Both MiMo runs and both
MiniMax name reads read REEFKIT as "REFKIT". Same image, same prompt, different verdicts from run
to run.

## Seed check
FERNKIT again with seed 6301 (`images-seed/`, $0.014, 3.6 s). By eye: the same picture. Files:
different (`cmp`: differ at byte 24; 279,491 vs 277,469 bytes). The seed fixes the picture, not
the file, the same as Prof. Kousen's October 20 result.

## Comparison image model
FERNKIT, seed 6301, on `google/gemini-3.1-flash-lite-image` (`images-nb/`): $0.03361975 from
`usage.cost`, 2.4 times FLUX, 3.6 s. It accepted `seed` and `aspect_ratio`. By my eye it met the
same six requirements, with no extra text.

## Step 5: the critic checked
**Second model (`--compare`)**: one image where the critics disagree.

| Image | Requirement | MiniMax | MiMo | What I saw |
|---|---|---|---|---|
| reefkit | The name is shown in a banner at the top | met | not met ("banner displays REFKIT") | met: REEFKIT in the banner |
| reefkit | There is no text other than the name | met | not met | met |

MiniMax's checklist said the banner was fine while its own narrow name read said "REFKIT": the
model disagreed with itself.

**Open-ended critique** (my own, at openrouter.ai/chat, MiniMax M3, CITYKIT image, "Critique this
image. What is wrong with it?"). What it claimed, and what was true:
- "CITYKIT" is garbled, probably a mangled "CITY KID": false. CITYKIT is the name the prompt asked
  for, spelled correctly; the checklist and both name reads agree.
- Headphones and a skateboard are present: true (both checklist items).
- Floating props, headphone geometry, two rendering styles on the skateboard, no ground shadow, a
  missing neck: style and anatomy claims the checklist does not ask about. Plausible, but none of
  them is a requirement.
- A chest emblem that copies a franchise's ball design: a claim worth checking against the team's
  "original creatures only" rule, which only a person looking can decide.

It never mentioned the four shared requirements or said whether they were met, and it invented a
name problem that does not exist.

**Which check caught what** (my words):
The person looking caught what both models missed: REEFKIT is spelled right, and both MiniMax and
MiMo read it as "REFKIT". The narrow name question compared in code is what turned that misread
into a visible flag, and the second model showed MiniMax's checklist contradicting its own name
read, so nothing passed silently. For Team Project 1 I would keep the narrow name question compared
in code plus the second model, with every flag going to a person, which is how our critic path
works.

## Linter (`ruff check .`, ruff 0.17.3)
- `week06/tests/test_generate.py`: I001, import block not sorted. Fixed ("Fix linter findings
  (week 6)").
- `.claude/hooks/guard.py`: PIE810, call `startswith` once with a tuple. Not fixed: it is the
  course's guard file, kept identical to the course copy.

## Total
FLUX $0.0840 (five images and the seed repeat), Gemini $0.0336, critics about $0.0080 including the
repeated run. About $0.13.
