"""The eval: every image in RECEIPT_DIR against RECEIPT_DIR/expected.json. Needs a key."""
import re

import pytest

from conftest import image_names

pytestmark = pytest.mark.model
IMAGES = image_names()


def words(name):
    return sorted(re.findall(r"[a-z0-9]+", (name or "").lower()))


def got(reads, name):
    receipt, usage, problems = reads(name)
    if receipt is None:
        pytest.fail("{}: {}".format(name, usage["error"]))
    return receipt, problems


def mismatch(name, field, model_value, key_value, problems):
    note = (" The checker finds no arithmetic problem on this read, so the key may be wrong: "
            "say so and stop; do not edit images/ or expected.json." if not problems else
            " The checker also reports: " + "; ".join(problems))
    return "{} {}: model read {!r}, key says {!r}.{}".format(name, field, model_value, key_value, note)


@pytest.mark.parametrize("name", IMAGES)
def test_total(reads, expected, name):
    receipt, problems = got(reads, name)
    key = expected[name]["total"]
    assert abs(receipt["total"] - key) <= 0.01, mismatch(name, "total", receipt["total"], key, problems)


@pytest.mark.parametrize("name", IMAGES)
def test_item_count(reads, expected, name):
    receipt, problems = got(reads, name)
    key = expected[name]["items"]
    assert len(receipt["items"]) == key, mismatch(name, "items", len(receipt["items"]), key, problems)


@pytest.mark.parametrize("name", IMAGES)
def test_merchant(reads, expected, name):
    receipt, problems = got(reads, name)
    key = expected[name]["merchant"]
    assert words(receipt["merchant"]) == words(key), mismatch(name, "merchant", receipt["merchant"], key, problems)


@pytest.mark.parametrize("name", IMAGES)
def test_date(reads, expected, name):
    receipt, problems = got(reads, name)
    key = expected[name]["date"]
    assert receipt["date"] == key, mismatch(name, "date", receipt["date"], key, problems)


@pytest.mark.parametrize("name", IMAGES)
def test_checker_finds_no_problems(reads, name):
    receipt, problems = got(reads, name)
    assert problems == [], "{}: {}".format(name, "; ".join(problems))
