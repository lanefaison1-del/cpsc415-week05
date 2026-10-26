# Checks

All runs on October 26, 2026, Python 3.9.6 in `.venv`, pytest 8.4.2.

## The test loop, red then green

Each step's tests were written and run before its code (one commit each, see the history).

| Step | Tests run before the code | After the code |
|---|---|---|
| 1. Checker | `ERROR tests/test_checker.py` (collection: no `checker` module), 1 error | 10 passed |
| 2. Parser | `ERROR tests/test_parser.py` (collection: no `reader` module), 1 error | 28 passed |
| 3. Vision call and eval | `ImportError: cannot import name 'read_receipt' from 'reader'` while loading `conftest.py` | 28 passed, 25 skipped (no key) |

Without a key, the 25 eval tests are skipped, not failed: `python -m pytest` gives `28 passed, 25 skipped`.

## The five course receipts, both models

One model call per image; each image is checked by five tests (total, item count, merchant, date, checker).

### `minimax/minimax-m3`, reasoning left on (default): 25 passed

| Receipt | Merchant read | Date | Items | Total | Checker | Tokens in | Tokens out | Finish |
|---|---|---|---|---|---|---|---|---|
| receipt-01.png | MATHER DINING HALL | 2026-10-02 | 3 | 13.66 | ok | 934 | 211 | stop |
| receipt-02.png | TRINITY BOOKSTORE | 2026-09-29 | 6 | 73.00 | ok | 934 | 541 | stop |
| receipt-03.png | LONG WALK COFFEE | 2026-10-06 | 3 | 11.01 | ok | 934 | 211 | stop |
| receipt-04.png | HARTFORD HARDWARE | 2026-10-04 | 4 | 33.52 | ok | 982 | 354 | stop |
| receipt-05.png | Bake Sale - CS Club | null | 3 | 6.50 | ok | 934 | 319 | stop |
| **Total** | | | | | | 4,718 | 1,636 | |

### `xiaomi/mimo-v2.6-flash`, `CHAT_REASONING=off`: 25 passed

| Receipt | Merchant read | Date | Items | Total | Checker | Tokens in | Tokens out | Finish |
|---|---|---|---|---|---|---|---|---|
| receipt-01.png | MATHER DINING HALL | 2026-10-02 | 3 | 13.66 | ok | 598 | 139 | stop |
| receipt-02.png | TRINITY BOOKSTORE | 2026-09-29 | 6 | 73.00 | ok | 598 | 216 | stop |
| receipt-03.png | LONG WALK COFFEE | 2026-10-06 | 3 | 11.01 | ok | 598 | 176 | stop |
| receipt-04.png | HARTFORD HARDWARE | 2026-10-04 | 4 | 33.52 | ok | 664 | 214 | stop |
| receipt-05.png | Bake Sale - CS Club | null | 3 | 6.50 | ok | 598 | 115 | stop |
| **Total** | | | | | | 3,056 | 860 | |

### What differed

- No receipt failed on either model, so there is no misread to explain on the course set. Both read the faded, tilted hardware receipt (receipt-04) correctly, including the two-digit year.
- MiMo used about a third fewer input tokens per image (598 against 934) and about half the output tokens, because with reasoning off it spends nothing on hidden thinking. MiniMax's output on receipt-02 (541 tokens, six items) was the largest single reply.
- Both models returned receipt-05's merchant as printed, "Bake Sale - CS Club", while the key says "CS Club Bake Sale". Under the draft spec (merchant ignoring case) both models would have failed that test. It is a spec ambiguity, not a misread; spec behavior 15 (same words in any order) settles it, and the test passes.
- Whatever sign each model gave the coffee shop's student discount, the reader stores it as a positive amount that is subtracted (behavior 7), and the checker found no problem on receipt-03 for either model.

## Linter

`ruff check .` (ruff 0.17.2, default rules) on the first green commit found 25 problems:

| Rule | Count | Where | What it means | Action |
|---|---|---|---|---|
| UP032 | 18 | `checker.py`, `reader.py`, tests | `.format()` where an f-string would do | Fixed: f-strings work on Python 3.9 |
| F401 | 1 | `reader.py` | `re` imported and never used | Fixed: removed |
| I001 | 2 | `tests/test_eval.py`, `tests/test_parser.py` | Imports out of order | Fixed |
| RUF100 | 2 | `tests/conftest.py` | `# noqa: E402` comments for a rule that is not enabled | Fixed: removed |
| RUF059 | 1 | `tests/test_eval.py` | Unpacked `receipt` never used | Fixed: renamed `_receipt` |
| PIE810 | 1 | `.claude/hooks/guard.py` | Two `startswith` calls could be one | Left as is: the hook is the course's copy |
