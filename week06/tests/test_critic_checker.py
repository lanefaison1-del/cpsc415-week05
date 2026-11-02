"""No-key tests for the critic-checker (spec.md, Week 6, behaviors 4-12 and 13).

The critiques here are written by hand; no model is called.
"""
import os
import subprocess
import sys
from pathlib import Path

from critique import check, disagreements, extract_json, text_matches

WEEK06 = Path(__file__).resolve().parents[1]
REQS = ["There is exactly one creature in the image", "The creature holds an acorn"]


def critique_with(*met):
    return {"checks": [{"requirement": r, "met": m, "evidence": "x"} for r, m in zip(REQS, met)]}


def test_4_all_met_is_ok():
    assert check(REQS, critique_with(True, True)) == {
        "ok": True, "problems": [], "unmet": [], "missing": [], "extra": []}


def test_5_unmet_requirement_is_reported_by_name():
    result = check(REQS, critique_with(True, False))
    assert not result["ok"]
    assert result["unmet"] == ["The creature holds an acorn"]


def test_5_anything_but_true_is_unmet():
    result = check(REQS, critique_with(True, "yes"))
    assert result["unmet"] == ["The creature holds an acorn"]


def test_6_unanswered_requirement_is_a_problem_even_if_the_rest_pass():
    result = check(REQS, {"checks": [{"requirement": REQS[0], "met": True}]})
    assert not result["ok"]
    assert result["missing"] == [REQS[1]]
    assert result["unmet"] == []


def test_7_invented_requirement_is_a_problem():
    c = critique_with(True, True)
    c["checks"].append({"requirement": "The lighting is dramatic", "met": True})
    result = check(REQS, c)
    assert not result["ok"]
    assert result["extra"] == ["The lighting is dramatic"]


def test_8_a_reply_that_is_not_json_is_a_failed_critique_not_a_crash():
    result = check(REQS, extract_json("Sorry, I can't see any image."))
    assert not result["ok"]
    assert result["missing"] == REQS
    assert check(REQS, extract_json(None))["missing"] == REQS
    assert check(REQS, {"verdict": "fine"})["missing"] == REQS


def test_9_json_inside_prose_and_a_fence_is_extracted():
    text = 'Here you go:\n```json\n{"checks": [{"requirement": "a", "met": true}]}\n```\nHope that helps.'
    assert extract_json(text) == {"checks": [{"requirement": "a", "met": True}]}


def test_10_requirement_text_is_matched_ignoring_case_and_punctuation():
    c = {"checks": [{"requirement": "there is exactly one creature in the image.", "met": True},
                    {"requirement": "The creature holds an ACORN", "met": True}]}
    assert check(REQS, c)["ok"]


def test_11_expected_text_is_compared_in_code():
    assert text_matches("FERNKIT", "  FernKit ")
    assert text_matches("AI Integration", "ai integration!")
    assert not text_matches("AI Integration", "AI Integratlon")   # the October 19 story
    assert not text_matches("FERNKIT", "FERNK1T")
    assert not text_matches("FERNKIT", "FERN KIT")
    assert not text_matches("FERNKIT", None)
    assert not text_matches("FERNKIT", "")


def test_12_two_critics_disagreeing_are_listed():
    a = [{"name": "fernkit", "critique": critique_with(True, True), "text_read": "FERNKIT"}]
    b = [{"name": "fernkit", "critique": critique_with(True, False), "text_read": "FERNK1T"}]
    d = disagreements(a, b)
    assert len(d) == 1
    assert {x["requirement"] for x in d[0]["diffs"]} == {REQS[1], "<text read>"}
    assert disagreements(a, a) == []


def test_13_no_key_no_critique():
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    r = subprocess.run([sys.executable, "critique.py", "images/manifest.json"], cwd=WEEK06, env=env,
                       capture_output=True, text=True, check=False)
    assert r.returncode == 1
    assert "OPENROUTER_API_KEY is not set" in r.stderr
