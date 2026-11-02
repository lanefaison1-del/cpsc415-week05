# Plan

## Files to create or change

| File | Purpose |
|---|---|
| `checker.py` | `check(receipt)`: the arithmetic checks, no model |
| `reader.py` | `parse_reply(text)`, `read_receipt(path)`, command line |
| `tests/test_checker.py` | No-key tests of the checker on hand-written receipts |
| `tests/test_parser.py` | No-key tests of `parse_reply` on hand-written replies |
| `tests/test_eval.py` | Model-marked eval over `RECEIPT_DIR`, skipped without a key |
| `tests/conftest.py` | The `model` marker, the skip rule, one model call per image per run |
| `pytest.ini` | Registers the `model` marker |
| `requirements-dev.txt` | `pytest`, `ruff` |
| `CHECKS.md` | Both models on the five receipts, linter, step 4, my receipts |
| `README.md` | How to run, results, step-4 story, my receipts |

## Order of work

1. Checker. Write `tests/test_checker.py` first and run it to see it fail, then `checker.py` until it passes.
2. Parser. Write `tests/test_parser.py` first and see it fail, then `parse_reply` in `reader.py`.
3. Vision call and eval. Write `tests/test_eval.py` and `conftest.py`, then `read_receipt` and the command line. Run the no-key tests, then the eval on `minimax/minimax-m3`, then on `xiaomi/mimo-v2.6-flash` with `CHAT_REASONING=off`.
4. Linter: `ruff check .`, record the findings, fix what is real.
5. Step 4: change receipt-01's total to 13.96 by hand, ask for the test to pass, record what happened, restore the key.
6. My own receipts in `my-receipts/` with a hand-written `expected.json`; eval on both models.

## Risks

- Step 1 rests on the line amount being `quantity × unit_price`. A receipt that prints only the line amount ("2.67") with no unit price would need the model to divide; if it rounds badly the checker reports a false problem. I would notice as a problem on a receipt whose printed numbers agree.
- Step 3 rests on the eval making one call per image. If each test called the model, five tests times five receipts is 25 calls instead of 5; I would notice in the token totals.
- The discount sign (behavior 7): if a model returns a positive discount for a receipt that printed it as a surcharge, the absolute value hides it. None of the course receipts has a surcharge.
- `expected.json` could itself be wrong. The eval would fail on a receipt the model read correctly; the fix is to say so and stop, never to edit the key (the hook enforces this). To make that visible, every eval failure prints the model's value next to the key's, and when the checker finds no arithmetic problem on that receipt the failure says the key may be wrong.
- Step 3 rests on both models returning content. `xiaomi/mimo-v2.6-flash` can spend its whole output budget on hidden reasoning and return an empty reply with `finish_reason: length`; it would show up as five failed reads. The eval table records `finish_reason` for every receipt, and MiMo runs with `CHAT_REASONING=off`.

## Proof

**Without a key** (`python -m pytest`; model tests show as skipped):

- `test_checker.py` proves the arithmetic: a receipt that adds up gives no problems; a wrong total, wrong subtotal, discount applied, no subtotal, quantity times unit price, and the one-cent tolerance each give the expected result. This proves the checker is right on its own, before any model is involved.
- `test_parser.py` proves the reply handling: clean JSON, JSON inside prose, JSON in a code fence, an empty reply, not JSON at all, a missing field, a negative discount, and a date with no year. This proves a bad reply is a failed read and not a crash.

**With a key** (`python -m pytest -m model`): the eval reads every image in `RECEIPT_DIR` and compares total, item count, merchant and date with `expected.json`, and that the checker finds no problems. This proves the model reads these images; it is the only part that can fail because of a model. When a receipt fails, the printed model value, key value and checker result together say whether the model misread the image, the spec was ambiguous, or the key itself is wrong; if it is the key, the run stops there and the key is not edited.

## Subagents and parallel work

None.

**Approved by:** Lane Faison, October 26, 2026

## Week 6: image set

### Files to create or change
| File | Purpose |
|---|---|
| `week06/critique.py` | `extract_json`, `check`, `text_matches`, `disagreements` (no model), then the vision call and the command line |
| `week06/generate.py` | `generate_one`, `run`, `summary`, the command line |
| `week06/tests/test_critic_checker.py` | No-key tests of the checker on hand-written critiques |
| `week06/tests/test_generate.py` | No-key tests of the generator with a fake Image API client |
| `week06/prompts.json` | The five prompts, seeds 6301–6305, requirements, expected names |
| `week06/images/` | The five FLUX images and `manifest.json` |
| `week06/images-seed/`, `week06/images-nb/` | The seed repeat of FERNKIT, and FERNKIT on Gemini |
| `week06/critique.json`, `week06/critique-mimo.json` | The two critics' answers |
| `week06/CHECKS.md` | Costs, verdicts, seed check, comparison model, step 5, linter, Review |
| `pytest.ini`, `requirements-dev.txt` | Collect `week06/tests` and put `week06/` on the import path; add `openrouter` |

Test files have names of their own (`test_critic_checker.py`, not `test_checker.py`) because the
Week 5 `tests/test_checker.py` already uses that name and pytest refuses two test modules with
the same name.

### Order of work
1. Checker: write `test_critic_checker.py`, run it to see it fail, then the checker part of
   `critique.py` until it passes. Commit `Image set: checker with tests`.
2. Generator: write `test_generate.py`, see it fail, then `generate.py`.
3. The vision call and the command line in `critique.py`. `ruff check .`; record what it finds.
4. Billed run: five FLUX images, then look at all five myself, reading each name letter by
   letter, before reading any critique, and write down what I saw for every image. Then five
   MiniMax critiques, the FERNKIT seed repeat, and FERNKIT on Gemini. Commit
   `Image set: five images, critiques, two image models`.
5. Step 5: the MiMo critique, `--compare`, every disagreement checked by eye, my open-ended
   critique of one image, and the three sentences. Commit `Image set: the critic checked`.
6. The team pull request, then the Review section of `CHECKS.md`, tag `week06-submitted`.

### Risks
- The critic says "unmet" when the image meets the requirement, or "met" when it does not. No
  no-key test can notice: those tests prove the checker reports what the critic said, not that
  the critic is right. Only the second model (`--compare`) or my own eyes catch it, which is why
  step 4 has me look before reading.
- MiMo spends its budget on hidden reasoning and replies empty. It would show as five failed
  critiques with `finish: length`; the SDK form `reasoning={"effort": "none"}` prevents it.
- Gemini rejects `seed` or `aspect_ratio`. The finding is that reproducibility is not on offer,
  not a bug; it goes in `CHECKS.md`.
- FLUX misspells a name. That is a correct finding for the text comparison, not a failure of
  the program; nothing is regenerated.
- Running a billed command in a loop by mistake. The commands make one call per prompt and stop
  without a key, and the tests never call a model.

### Proof
**Without a key** (`python -m pytest`, free, under a second):
- `test_critic_checker.py`: all met; one unmet, named; one requirement unanswered; one invented;
  a reply that is not JSON; JSON inside prose and a fence; loose requirement matching; the text
  comparison (`"AI Integration"` against `"AI Integratlon"`, and `"FERNKIT"` against
  `"FERNK1T"`); two critics disagreeing. This proves the checker turns any critique into the
  right verdict.
- `test_generate.py`: one call per prompt with the prompt and seed as given, every manifest
  field, a missing cost recorded as `null` and reported, `--only` makes one call, a reply with no
  image is a clear error, a failure partway keeps the manifest, and no key means no call. This
  proves what was asked for and paid for is recorded.

**With a key** (by hand, once each, about $0.13): five FLUX generations, five MiniMax critiques
(checklist and banner read), five MiMo critiques, one seed repeat, one Gemini image. This proves
what these models actually do on my prompts, and is the only part that costs money.

- **A wrong verdict from the critic** (unmet when it is met, or the reverse) is caught by no test.
  `CHECKS.md` therefore has a "what I saw" column for every image, my own verdict beside the
  critic's, not only for the images where MiniMax and MiMo disagree.
- **The seed check:** FERNKIT again with seed 6301 into `images-seed/`, compared two ways: the
  two pictures side by side by eye, and the two files with `cmp`. Both results go in `CHECKS.md`;
  the same picture with different file bytes means the seed fixes the picture, not the file.

### Subagents and parallel work
None.

**Approved by:** Lane Faison, 2026-11-02
