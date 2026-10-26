# Project conventions

## What this repository is

The Week 5 lab for CPSC 415: a command-line program that reads a photograph of a receipt with a vision model, returns the receipt as JSON, and checks in plain code that the items add up to the subtotal and that subtotal, discount and tax produce the total. It reports problems; it never fixes them. The intent is in [`intent/receipts.md`](intent/receipts.md) and the design in [`spec.md`](spec.md).

## Commands

```
# build: python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
# test:  .venv/bin/python -m pytest              (no key: model tests are skipped)
# eval:  .venv/bin/python -m pytest -m model -s  (needs OPENROUTER_API_KEY)
# run:   python3 reader.py images/receipt-01.png
# lint:  .venv/bin/ruff check .
```

## Conventions

- Language: Python; code must run on Python 3.9 or later. The program uses the standard library only; pytest and ruff are dev-only.
- Default chat model: `minimax/minimax-m3` through OpenRouter, compared with `xiaomi/mimo-v2.6-flash`. Final choices and reasons are recorded in `spec.md`.
- Configuration comes only from the environment: `OPENROUTER_API_KEY`, `CHAT_BASE_URL`, `CHAT_MODEL`, `CHAT_REASONING`, `RECEIPT_DIR`. No key or secret in code or in the repo.
- File naming: lowercase snake_case. Tests are `tests/test_<module>.py`.
- Run results go in `CHECKS.md`.

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- This is the Week 5 introductory lab. Stages assigned: intent, spec, plan,
  and tests. No branches or pull requests yet. Commit to main.
- Libraries and build tools are allowed. Name each dependency in spec.md
  under Dependencies, with the reason, before installing it; a hook blocks
  installs that spec.md does not list.
- images/ and images/expected.json are the answer key. Never edit them. If
  a test disagrees with the key, say so and stop.
- Tests live in tests/ (Python) or src/test (Java). Tests that call a model
  are marked and are skipped when no API key is set.
- Ensure all commits are authored by Lane Faison.
- Course requirement: intent and spec come before code, and `plan.md` is approved before implementation starts. Tests are written and run before the code they test.
- Never commit `.env` or `.claude/settings.local.json`.

## Common mistakes

Previous bugs to avoid. Add to this list as they happen.

- Sending `"reasoning": {"enabled": false}` to every model: it fixes MiMo's empty replies but stops MiniMax reading the faded date. It is a per-model setting.
- Calling the model once per test instead of once per image.
