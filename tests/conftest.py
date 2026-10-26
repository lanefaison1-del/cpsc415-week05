"""Shared setup: the model marker, the skip rule, and one model call per image per run."""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from checker import check
from reader import DEFAULT_MODEL, read_receipt

RESULTS = {}


def receipt_dir():
    return ROOT / os.environ.get("RECEIPT_DIR", "images")


def image_names():
    folder = receipt_dir()
    return sorted(p.name for p in folder.iterdir()
                  if p.suffix.lower() in (".png", ".jpg", ".jpeg")) if folder.is_dir() else []


def pytest_collection_modifyitems(config, items):
    if os.environ.get("OPENROUTER_API_KEY"):
        return
    skip = pytest.mark.skip(reason="needs OPENROUTER_API_KEY")
    for item in items:
        if "model" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def expected():
    return json.loads((receipt_dir() / "expected.json").read_text())


@pytest.fixture(scope="session")
def reads():
    """Read each image once per run, however many tests look at it."""
    cache = {}

    def get(name):
        if name not in cache:
            receipt, usage = read_receipt(receipt_dir() / name)
            problems = check(receipt) if receipt is not None else None
            cache[name] = (receipt, usage, problems)
            RESULTS[name] = cache[name]
        return cache[name]
    return get


def pytest_terminal_summary(terminalreporter):
    if not RESULTS:
        return
    tr = terminalreporter
    tr.write_line("")
    tr.write_line("model {}, reasoning {}, folder {}".format(
        os.environ.get("CHAT_MODEL", DEFAULT_MODEL), os.environ.get("CHAT_REASONING", "default"),
        os.environ.get("RECEIPT_DIR", "images")))
    tr.write_line("| Receipt | Merchant | Date | Items | Total | Checker | Tokens in | Tokens out | Finish |")
    tr.write_line("|---|---|---|---|---|---|---|---|---|")
    tin = tout = 0
    for name in sorted(RESULTS):
        receipt, usage, problems = RESULTS[name]
        tin += usage["prompt_tokens"] or 0
        tout += usage["completion_tokens"] or 0
        if receipt is None:
            tr.write_line("| {} | failed read: {} | | | | | {} | {} | {} |".format(
                name, usage["error"], usage["prompt_tokens"], usage["completion_tokens"], usage["finish_reason"]))
            continue
        tr.write_line("| {} | {} | {} | {} | {:.2f} | {} | {} | {} | {} |".format(
            name, receipt["merchant"], receipt["date"], len(receipt["items"]), receipt["total"],
            "ok" if not problems else "; ".join(problems), usage["prompt_tokens"],
            usage["completion_tokens"], usage["finish_reason"]))
    tr.write_line(f"| **Total** | | | | | | {tin} | {tout} | |")
