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
- `expected.json` could itself be wrong. The eval would fail on a receipt the model read correctly; the fix is to say so and stop, never to edit the key (the hook enforces this).

## Proof

**Without a key** (`python -m pytest`; model tests show as skipped):

- `test_checker.py` proves the arithmetic: a receipt that adds up gives no problems; a wrong total, wrong subtotal, discount applied, no subtotal, quantity times unit price, and the one-cent tolerance each give the expected result. This proves the checker is right on its own, before any model is involved.
- `test_parser.py` proves the reply handling: clean JSON, JSON inside prose, JSON in a code fence, an empty reply, not JSON at all, a missing field, a negative discount, and a date with no year. This proves a bad reply is a failed read and not a crash.

**With a key** (`python -m pytest -m model`): the eval reads every image in `RECEIPT_DIR` and compares total, item count, merchant and date with `expected.json`, and that the checker finds no problems. This proves the model reads these images; it is the only part that can fail because of a model.

## Subagents and parallel work

None.

**Approved by:** <your name>, <date>
