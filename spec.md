# Spec

## Intent

Implements [`intent/receipts.md`](intent/receipts.md).

## Components

### Reader (`reader.py`)

- **What it does:** Sends one receipt image to a vision model with a prompt that asks for JSON only, takes the JSON out of the reply, and turns it into a receipt dictionary with a fixed set of fields. It reads; it does no arithmetic.
- **Language:** Python 3.9 or later. **Why:** Weeks 2 to 4 were Python, so the OpenRouter request code and the Keychain key loading are already proven on my machine, and the standard library covers HTTP, base64 and JSON. Java with JUnit was the alternative; it adds a Gradle build for a program this small and no benefit.
- **Model:** `minimax/minimax-m3` (default) compared with `xiaomi/mimo-v2.6-flash`, both through OpenRouter. **Why:** both accept images and both are the class models. MiniMax passed all five Week 3 cases and reads the faded date only with reasoning on; MiMo is cheaper but in October started spending its whole output budget on hidden reasoning. The run on all five receipts with both models is in `CHECKS.md`.
- **Reasoning setting:** `CHAT_REASONING=off` adds `"reasoning": {"enabled": false}` to the request. It is off for `xiaomi/mimo-v2.6-flash` (otherwise the reply is empty with `finish_reason: length`) and left unset for `minimax/minimax-m3` (with reasoning off it stops reading the faded date). It is a setting, not a code branch on the model name.
- **Interfaces:** `read_receipt(path)` returns `(receipt, usage)`, where `receipt` is the dictionary below or `None` for a failed read, and `usage` has `prompt_tokens`, `completion_tokens`, `finish_reason` and `error`. Command line: `python reader.py path/to/image.png` prints the receipt JSON, the checker's problems, and a usage line. Settings: `OPENROUTER_API_KEY`, `CHAT_BASE_URL` (default `https://openrouter.ai/api/v1`), `CHAT_MODEL` (default `minimax/minimax-m3`), `CHAT_REASONING`, `RECEIPT_DIR` (eval only, default `images`).
- **Receipt fields:** `merchant` (string), `date` (`YYYY-MM-DD` or null), `items` (list of `{name, quantity, unit_price}`), `subtotal` (number or null), `discount` (number, 0 when none), `tax` (number, 0 when none), `total` (number).

### Checker (`checker.py`)

- **What it does:** Takes a receipt dictionary and returns a list of problems in plain English. Plain code, no model, no network. It never changes the receipt.
- **Language:** Python 3.9 or later, same as the reader.
- **Model:** none. The point of the checker is that the arithmetic is not trusted to a model.
- **Interfaces:** `check(receipt)` returns a list of strings; an empty list means the receipt adds up.

## Dependencies

- `pytest` (pip, dev only, in `requirements-dev.txt`). **Reason:** test discovery, markers to skip model tests without a key, and a session-scoped fixture so the eval calls the model once per image, not once per test. By hand this would be a `unittest` runner with its own skip logic and caching.
- `ruff` (pip, dev only, in `requirements-dev.txt`). **Reason:** the lab's linter step (`ruff check .`). Not needed to run the program.
- Everything the program itself uses is standard library: `urllib.request`, `base64`, `json`, `re`, `os`, `pathlib`, `sys`.

## Behavior

1. The reader sends the image as a base64 data URL content part next to the prompt text, in one chat request per image.
2. The prompt asks for one JSON object with exactly the receipt fields, money as plain numbers, the date as `YYYY-MM-DD`, and nothing else.
3. A reply that is not JSON is a failed read, not a crash: the reader returns `None` with the reason in `usage["error"]`, and the command line prints it and exits 1.
4. A reply with JSON inside prose or a code fence still parses: the reader takes the text from the first `{` to the last `}`.
5. A reply missing `merchant`, `items` or `total`, or with a non-numeric amount, is a failed read with the field named.
6. The date is null when the year is not printed on the receipt; the prompt says so, and the reader turns any date that is not a valid `YYYY-MM-DD` into null. A two-digit year counts as printed (`10/04/26` is `2026-10-04`).
7. A discount is stored as a positive amount: the reader takes the absolute value whatever sign the model returns. Missing `discount` or `tax` becomes 0.
8. An item is one printed line; its line amount is `quantity × unit_price`, rounded to cents. A missing quantity is 1.
9. The checker reports when the line amounts do not add up to the subtotal, with both numbers and the difference.
10. The checker reports when `subtotal − discount + tax` does not equal the total, with both numbers and the difference.
11. When there is no subtotal, the checker compares the line amounts, minus discount, plus tax, with the total directly.
12. Two amounts agree when they differ by at most $0.01.
13. The checker reports a negative total or an item with quantity below 1, and returns problems; it never raises on a well-formed receipt.
14. The eval reads every image in `RECEIPT_DIR` once, compares each with `RECEIPT_DIR/expected.json` (total within one cent, number of items, merchant ignoring case, date) and asserts the checker reports no problems. It prints a per-receipt table with tokens in and out.

## Failure handling

- No `OPENROUTER_API_KEY`: the command line stops with a one-line message; model tests are skipped, not failed.
- HTTP error, timeout (60 s) or empty reply: a failed read with the status or `finish_reason` in `usage["error"]`.
- A model that misreads a number: the checker catches it if the arithmetic no longer agrees; if the misread still adds up (a wrong total and a matching wrong subtotal), only the eval against `expected.json` catches it.

## Cost estimate

About 700 to 1,000 tokens in and 150 to 400 out per receipt. At under $1 per million tokens for both models that is under $0.001 per receipt; ten receipts on two models, twice, is about a cent.

## Out of scope

Carried from the intent: correcting receipts, payment details, multi-receipt images, currency. Also ruled out: `response_format` JSON schema (an early-finish experiment, not the default), and a retry loop on a failed read.
