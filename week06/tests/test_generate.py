"""No-key tests for the generator (spec.md, Week 6, behaviors 1-3 and 13). The Image API is a fake."""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from generate import run, summary

WEEK06 = Path(__file__).resolve().parents[1]
PROMPTS = [
    {"name": "fernkit", "prompt": "a forest fox kit", "seed": 6301, "requirements": ["r1"], "expected_text": "FERNKIT"},
    {"name": "dunekit", "prompt": "a desert fox kit", "seed": 6302, "requirements": ["r2"], "expected_text": "DUNEKIT"},
]


class FakeImages:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        item = SimpleNamespace(b64_json=base64.b64encode(b"fake-jpeg").decode(), media_type="image/jpeg")
        return SimpleNamespace(data=[item], usage=SimpleNamespace(cost=0.014))


def fake_client(images=None):
    return SimpleNamespace(images=images or FakeImages())


def test_1_one_call_per_prompt_with_its_prompt_seed_and_model(tmp_path):
    client = fake_client()
    run(client, PROMPTS, tmp_path, "black-forest-labs/flux.2-klein-4b")
    assert [(c["prompt"], c["seed"], c["model"]) for c in client.images.calls] == [
        ("a forest fox kit", 6301, "black-forest-labs/flux.2-klein-4b"),
        ("a desert fox kit", 6302, "black-forest-labs/flux.2-klein-4b")]


def test_1_only_makes_one_call(tmp_path):
    client = fake_client()
    assert [e["name"] for e in run(client, PROMPTS, tmp_path, "m", only="dunekit")] == ["dunekit"]
    assert len(client.images.calls) == 1


def test_2_every_manifest_field_and_the_image_saved(tmp_path):
    manifest = run(fake_client(), PROMPTS, tmp_path, "m")
    for entry in manifest:
        for field in ("name", "prompt", "seed", "requirements", "expected_text", "model", "aspect_ratio",
                      "file", "media_type", "cost", "seconds"):
            assert field in entry
        assert entry["cost"] == 0.014
        assert (tmp_path / entry["file"]).read_bytes() == b"fake-jpeg"
    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest


def test_2_missing_cost_is_null_and_reported(tmp_path):
    class NoCost(FakeImages):
        def generate(self, **kwargs):
            r = super().generate(**kwargs)
            r.usage = None
            return r

    manifest = run(fake_client(NoCost()), PROMPTS[:1], tmp_path, "m")
    assert manifest[0]["cost"] is None
    assert summary(manifest) == "1 image(s), $0.0000 total, cost missing for 1 image(s)"
    assert summary([{"cost": 0.014}, {"cost": 0.014}]) == "2 image(s), $0.0280 total"


def test_3_a_reply_with_no_image_is_a_clear_error(tmp_path):
    class Empty(FakeImages):
        def generate(self, **kwargs):
            r = super().generate(**kwargs)
            r.data = []
            return r

    with pytest.raises(RuntimeError, match="m returned no image"):
        run(fake_client(Empty()), PROMPTS, tmp_path, "m")


def test_3_a_failure_partway_keeps_the_manifest(tmp_path):
    class FailSecond(FakeImages):
        def generate(self, **kwargs):
            if self.calls:
                raise RuntimeError("model rejected the request")
            return super().generate(**kwargs)

    with pytest.raises(RuntimeError, match="rejected"):
        run(fake_client(FailSecond()), PROMPTS, tmp_path, "m")
    assert [e["name"] for e in json.loads((tmp_path / "manifest.json").read_text())] == ["fernkit"]


def test_13_no_key_no_call(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    r = subprocess.run([sys.executable, "generate.py", "prompts.json", "--out", str(tmp_path)], cwd=WEEK06,
                       env=env, capture_output=True, text=True, check=False)
    assert r.returncode == 1
    assert "OPENROUTER_API_KEY is not set" in r.stderr
    assert not (tmp_path / "manifest.json").exists()
