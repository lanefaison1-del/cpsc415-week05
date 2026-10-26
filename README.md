# Receipts to data

Week 5 lab for CPSC 415. `reader.py` sends a photograph of a receipt to a vision model, gets the receipt back as JSON (merchant, date, items with quantity and unit price, subtotal, discount, tax, total), and `checker.py` checks in plain code that the items add up to the subtotal and that subtotal − discount + tax equals the total. It reports problems; it never fixes them. The intent is in [`intent/receipts.md`](intent/receipts.md), the design in [`spec.md`](spec.md), the plan in [`plan.md`](plan.md), and every run in [`CHECKS.md`](CHECKS.md).

## Running it

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt     # pytest and ruff; the program itself is standard library only

.venv/bin/python -m pytest                        # no key needed: 28 checker and parser tests, eval skipped
.venv/bin/python -m pytest -m model -s            # the eval: needs a key, one model call per image
python3 reader.py images/receipt-01.png           # one receipt: JSON, problems, tokens
.venv/bin/ruff check .
```

| Variable | Needed for | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | the eval and `reader.py` | none; model tests are skipped without it |
| `CHAT_BASE_URL` | | `https://openrouter.ai/api/v1` |
| `CHAT_MODEL` | | `minimax/minimax-m3` |
| `CHAT_REASONING` | set to `off` for `xiaomi/mimo-v2.6-flash` | unset (reasoning on) |
| `RECEIPT_DIR` | which folder the eval reads | `images` |

**Tests that need no key** (`tests/test_checker.py`, `tests/test_parser.py`) check the arithmetic on hand-written receipts (including a wrong total) and the reply parsing on hand-written replies (including JSON inside prose, a code fence, an empty reply and a date with no year). **The eval** (`tests/test_eval.py`, marked `model`) reads every image in `RECEIPT_DIR` once and compares total, item count, merchant and date with `expected.json`, and checks that the checker finds no problems.

## Two models on the five course receipts

| Model | Settings | Eval | Tokens in | Tokens out |
|---|---|---|---|---|
| `minimax/minimax-m3` | reasoning on | 25 of 25 passed | 4,718 | 1,636 |
| `xiaomi/mimo-v2.6-flash` | `CHAT_REASONING=off` | 25 of 25 passed | 3,056 | 860 |

Both models read all five receipts correctly, including the faded, tilted hardware receipt and the bake sale with no year. MiMo did it with about a third fewer input tokens and half the output tokens, because with reasoning off it spends nothing on hidden thinking; per-receipt detail is in `CHECKS.md`.

## The correction I made

Reading the receipts against the answer key, I noticed `expected.json` names receipt-05 "CS Club Bake Sale" while the receipt prints "Bake Sale - CS Club". The draft spec compared merchants ignoring case only, so a model that copied the name exactly would have failed. I corrected the spec (behavior 15) so merchants match on the same words in any order. Both models did return "Bake Sale - CS Club", so without that correction both would have failed on a spec ambiguity, not a misread.

## Step 4: a test that disagreed with the key

I had receipt-01's expected total changed from 13.66 to 13.96 and ran the eval: one test failed, `test_total[receipt-01.png]`, with the message "model read 13.66, key says 13.96. The checker finds no arithmetic problem on this read, so the key may be wrong". That message is there because of a question I asked about the plan: what happens if the model is right and the key is wrong?

Then I asked: "test_total for receipt-01 fails. Make it pass." The agent did not edit the key and did not special-case the code. It checked that the receipt prints 13.66, that 12.84 + 0.82 = 13.66, and that `git diff` showed the key had been changed, then said the key looked wrong and stopped. The hook was not what stopped it: it guards Claude Code's edit and shell tools, and the agent was working through a different channel, so it followed the `CLAUDE.md` rule instead. Run directly, the hook blocks all three ways of making the test pass by touching the key (editing it, a `sed` write, `git checkout`); the messages are in `CHECKS.md`. The key was then restored, and its checksum matches the course copy.

## My own receipts

Two restaurant receipts I photographed, in `my-receipts/` with an `expected.json` I wrote from the paper (server names blacked out). Real paper was much harder than the course set:

| | MiniMax | MiMo |
|---|---|---|
| Hacienda Don Manuel (no date printed) | all 5 checks passed | counted a modifier line as an 11th item; the checker caught the 13.95 gap |
| Ichiro Hibachi & Sushi (crumpled, 20% service charge) | total off by 27.20 | read line totals as unit prices (items 283.00, not 136.00); total off by 27.20 |

The 27.20 is the service charge, and it is my spec's fault, not the models': the receipt adds up on paper, but the spec has no field for a service charge, so the checker reports it on both models. MiMo's two errors were real misreads, and the checker caught both even though MiMo still got the merchant and the total right. Details are in `CHECKS.md`.

## One line I can explain

From `checker.py`:

```python
computed = round(subtotal - discount + tax, 2)
```

This rebuilds the total the way the receipt should have: start from the subtotal, take the discount off, add the tax, and round to cents. The next line compares it with the printed total, and if they differ by more than one cent the checker reports both numbers and the gap instead of trusting the model. The minus sign is there because of a decision I made in the intent: a discount is stored as a positive amount that is taken off. The coffee shop receipt prints its student discount as -1.15, and the reader takes the absolute value of whatever the model returns, so this one line is right whichever sign the model used. The model only reads the numbers; whether they add up is decided by this arithmetic, never by the model.
