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
14. The eval reads every image in `RECEIPT_DIR` once, compares each with `RECEIPT_DIR/expected.json` (total within one cent, number of items, merchant, date) and asserts the checker reports no problems. It prints a per-receipt table with tokens in and out.
15. Merchants match when they have the same words in any order, ignoring case and punctuation. The key writes receipt-05 as "CS Club Bake Sale" while the receipt prints "Bake Sale - CS Club"; both are the same merchant, and a model that copies the printed name has read it correctly.

## Failure handling

- No `OPENROUTER_API_KEY`: the command line stops with a one-line message; model tests are skipped, not failed.
- HTTP error, timeout (60 s) or empty reply: a failed read with the status or `finish_reason` in `usage["error"]`.
- A model that misreads a number: the checker catches it if the arithmetic no longer agrees; if the misread still adds up (a wrong total and a matching wrong subtotal), only the eval against `expected.json` catches it.

## Cost estimate

About 700 to 1,000 tokens in and 150 to 400 out per receipt. At under $1 per million tokens for both models that is under $0.001 per receipt; ten receipts on two models, twice, is about a cent.

## Out of scope

Carried from the intent: correcting receipts, payment details, multi-receipt images, currency. Also ruled out: `response_format` JSON schema (an early-finish experiment, not the default), and a retry loop on a failed read.

## Week 6: image set

Implements [`intent/image-set.md`](intent/image-set.md). Everything lives in `week06/`.

### Generator (`week06/generate.py`)
- **What it does:** makes one Image API call per prompt in `prompts.json`, saves each image, and
  writes `manifest.json` beside the images with what was asked for and what it cost.
- **Language:** Python 3.11 in `.venv`. **Why:** the `openrouter` SDK and the course examples are
  Python, my Weeks 2–5 code is Python, and the team project's generator is Python, so my prompts
  file works in both places. Java was the alternative; it has no OpenRouter SDK, so I would write
  the Image API request by hand.
- **Model:** `black-forest-labs/flux.2-klein-4b` by default, compared with
  `google/gemini-3.1-flash-lite-image` on FERNKIT, seed 6301. **Why:** FLUX is the class image
  model, about $0.014 per image, and accepts a seed. Gemini is priced per image token (about
  $0.034 for one 1:1 image in class) and adds a SynthID watermark. The comparison's cost and
  verdict go in `week06/CHECKS.md`.
- **Interfaces:** `generate_one(client, model, prompt, seed, aspect_ratio="1:1")` returns
  `{"bytes", "media_type", "cost"}`; `run(client, prompts, out, model, aspect_ratio="1:1",
  only=None)` returns the manifest. Command line:
  `python generate.py prompts.json --out DIR [--model SLUG] [--only NAME]`. Manifest entry:
  `name`, `prompt`, `seed`, `requirements`, `expected_text`, `model`, `aspect_ratio`, `file`,
  `media_type`, `cost`, `seconds`.

### Critic-checker (`week06/critique.py`)
- **What it does:** sends each image with a yes/no checklist made from its requirements to a
  vision model, takes the JSON out of the reply, and compares the checklist with the requirements
  in plain code. A second, narrow question asks the model to write the name shown in the banner at
  the top exactly as printed, and the code compares that with the expected name. It asks for the
  banner, not the largest text: a creature's gear (a skateboard, a scarf) could carry larger text. `--compare` lists where two
  critique files disagree.
- **Language:** Python 3.11, same as the generator; it reuses the same SDK client.
- **Model:** `minimax/minimax-m3` as the critic, checked by `xiaomi/mimo-v2.6-flash`. **Why:**
  both are the class vision models I compared in Week 5. MiniMax read the faded receipt date
  only with its reasoning on, so it runs with reasoning on. MiMo is cheaper and from a different
  vendor, which makes it a second opinion rather than a repeat; it runs with
  `reasoning={"effort": "none"}`, the SDK form of `{"enabled": false}`, or its reply comes back
  empty.
- **Interfaces:** `extract_json(text)` returns a dict or `None`; `check(requirements, critique)`
  returns `{"ok", "problems", "unmet", "missing", "extra"}`; `text_matches(expected, read)`
  returns a bool; `disagreements(a, b)` returns a list of images, each with the requirements on
  which the two files differ. Command line: `python critique.py images/manifest.json [--model
  SLUG] [--out FILE]` and `python critique.py --compare A.json B.json`.

### Behavior (no key unless marked)
1. The generator makes exactly one call per prompt, with that prompt's text, seed, and the model
   given; `--only NAME` makes exactly one call.
2. Every manifest entry has all the fields above. `cost` is the reply's `usage.cost`, or `null`
   when the reply has none; the summary line says how many costs were missing instead of counting
   them as $0.
3. `manifest.json` is written after every image, so a failure partway keeps the record of the
   images already paid for. A reply with no image raises an error that names the model.
4. A critique in which every requirement is answered and met is ok.
5. A requirement answered with anything other than `true` is reported unmet, by name.
6. A requirement the critic did not answer is a problem, even when every answered one is met.
7. An item the critic answered that was not asked for (an invented requirement) is a problem.
8. A critique that is not JSON is a failed critique, not a crash: every requirement counts as
   unanswered.
9. JSON inside prose or a code fence is still extracted.
10. Requirement text is matched ignoring case and punctuation.
11. Expected text is compared in code, not by the critic: the banner name the model read is
    compared with `expected_text` ignoring case and punctuation. "AI Integration" against
    "AI Integratlon" is a mismatch, and so is no reply.
12. `--compare` lists every image and requirement where two critique files disagree, including
    the banner text read, without a key.
13. Without `OPENROUTER_API_KEY`, `generate.py` and `critique.py` each print one line saying so
    and exit 1; nothing is billed.
14. (Key, by hand.) The five FLUX images, one seed repeat, one Gemini image, and critiques from
    both vision models, run once each, are in `week06/` with their costs in `CHECKS.md`.

### Failure handling
A model that rejects `seed` or `aspect_ratio`, an HTTP error, or a timeout raises; the error is
shown and nothing is retried. An empty reply or `finish_reason: length` from the critic is a
failed critique (behavior 8) with the finish reason recorded.

### Cost
Five FLUX images about $0.07, the seed repeat $0.014, one Gemini image about $0.034, two critic
calls per image on MiniMax (checklist and banner read) about $0.0015 per image, MiMo less. One
full run is about $0.13.

### Dependencies (Week 6)
- `openrouter` (pip, in `requirements-dev.txt`). **Reason:** the official OpenRouter SDK:
  `client.images.generate` for the Image API and `client.chat.send` for the vision critique, one
  client for both request shapes. By hand it would be two `urllib.request` calls with my own JSON,
  base64, and error handling, as in Weeks 2–5. It requires Python 3.10 or later, so `.venv` is
  now Python 3.11.
