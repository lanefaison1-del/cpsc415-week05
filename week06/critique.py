"""Critique an image set with a vision model, then check the critique in code (spec.md, Week 6).

    python critique.py images/manifest.json                        # minimax/minimax-m3, writes critique.json
    python critique.py images/manifest.json --model xiaomi/mimo-v2.6-flash --out critique-mimo.json
    python critique.py --compare critique.json critique-mimo.json  # no key: where the two critics disagree

Each image goes to the vision model with a yes/no checklist made from its requirements, and the
reply must be JSON. The code then checks the checklist: every requirement answered, none invented,
each one met. A second, narrow question asks for the name in the banner, and the code compares it
with the name the prompt asked for. A critique that is not JSON is a failed critique, not a crash.
"""
import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_MODEL = "minimax/minimax-m3"
# Hidden reasoning is a per-model setting: MiMo replies empty with it on, MiniMax reads worse with
# it off. The SDK only knows "effort", so {"effort": "none"} is its form of {"enabled": false}.
REASONING = {"xiaomi/mimo-v2.6-flash": {"effort": "none"}}

CHECKLIST_PROMPT = """You are checking a generated image against the prompt that produced it.
Prompt: {prompt}

Answer every item below with true or false, strictly from what is visible in the image.
Reply with one JSON object and nothing else:
{{"checks": [{{"requirement": "<item text, copied exactly>", "met": true, "evidence": "<one short sentence>"}}, ...]}}

Items:
{items}"""

TEXT_PROMPT = ("Write the name shown in the banner at the top of this image exactly as printed, "
               "character for character. Reply with that text only.")


# ---------- plain code: no model, no key ----------

def extract_json(text: str | None) -> dict | None:
    """The JSON object inside a reply, or None. Models wrap JSON in prose or code fences."""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def check(requirements: list, critique: dict | None) -> dict:
    """Compare the critic's checklist with the requirements: what the code can say for sure."""
    if critique is None or not isinstance(critique.get("checks"), list):
        return {"ok": False, "problems": ["critique was not the JSON checklist that was asked for"],
                "unmet": [], "missing": list(requirements), "extra": []}
    answered = {}
    for c in critique["checks"]:
        if isinstance(c, dict) and isinstance(c.get("requirement"), str):
            answered[_norm(c["requirement"])] = c
    wanted = {_norm(r): r for r in requirements}
    missing = [r for k, r in wanted.items() if k not in answered]
    extra = [c["requirement"] for k, c in answered.items() if k not in wanted]
    unmet = [r for k, r in wanted.items() if k in answered and answered[k].get("met") is not True]
    problems = []
    if missing:
        problems.append(f"critic did not answer {len(missing)} requirement(s)")
    if extra:
        problems.append(f"critic answered {len(extra)} item(s) that were not asked")
    if unmet:
        problems.append(f"{len(unmet)} requirement(s) reported unmet")
    return {"ok": not problems, "problems": problems, "unmet": unmet, "missing": missing, "extra": extra}


def text_matches(expected: str, read: str | None) -> bool:
    """The name the model read against the one asked for, ignoring case and punctuation.
    A space inside the name ("FERN KIT") is a mismatch."""
    if not read:
        return False
    return _norm(expected) == _norm(read)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def disagreements(a: list, b: list) -> list:
    """Images where two critique files differ on any requirement or on the name read."""
    out = []
    by_name = {e["name"]: e for e in b}
    for ea in a:
        eb = by_name.get(ea["name"])
        if eb is None:
            continue
        va, vb = _verdicts(ea), _verdicts(eb)
        diffs = [{"requirement": r, "a": va.get(r), "b": vb.get(r)}
                 for r in sorted(set(va) | set(vb)) if va.get(r) != vb.get(r)]
        if ea.get("text_read") != eb.get("text_read"):
            diffs.append({"requirement": "<text read>", "a": ea.get("text_read"), "b": eb.get("text_read")})
        if diffs:
            out.append({"name": ea["name"], "diffs": diffs})
    return out


def _verdicts(entry: dict) -> dict:
    checks = (entry.get("critique") or {}).get("checks") or []
    return {c.get("requirement"): c.get("met") for c in checks if isinstance(c, dict)}


# ---------- the billed part ----------

def ask(client, model: str, image_path: Path, media_type: str, question: str, max_tokens: int = 1500):
    """One vision call through the chat endpoint: the question plus the image as a data URL."""
    data = base64.b64encode(image_path.read_bytes()).decode()
    kwargs = {"reasoning": REASONING[model]} if model in REASONING else {}
    c = client.chat.send(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{data}"}}]}], **kwargs)
    usage = {"in": c.usage.prompt_tokens, "out": c.usage.completion_tokens,
             "cost": getattr(c.usage, "cost", None)} if c.usage else {}
    usage["finish"] = c.choices[0].finish_reason      # "length": the budget ran out mid-answer
    return c.choices[0].message.content, usage


def critique_set(client, model: str, manifest_path: Path) -> list:
    """One checklist call and one banner read per image in the manifest."""
    results = []
    for entry in json.loads(manifest_path.read_text()):
        image = manifest_path.parent / entry["file"]
        items = "\n".join(f"- {r}" for r in entry["requirements"])
        raw, usage = ask(client, model, image, entry["media_type"],
                         CHECKLIST_PROMPT.format(prompt=entry["prompt"], items=items))
        critique = extract_json(raw)
        result = {"name": entry["name"], "model": model, "critique": critique, "raw": raw,
                  "usage": usage, "check": check(entry["requirements"], critique)}
        if entry.get("expected_text"):
            read, usage_text = ask(client, model, image, entry["media_type"], TEXT_PROMPT, max_tokens=400)
            result["text_read"] = (read or "").strip()
            result["text_matches"] = text_matches(entry["expected_text"], read)
            result["usage_text"] = usage_text
        results.append(result)
        verdict = "ok" if result["check"]["ok"] else "; ".join(result["check"]["problems"])
        name = "" if "text_read" not in result else \
            f"  name read: {result['text_read']!r} ({'match' if result['text_matches'] else 'MISMATCH'})"
        print(f"{entry['name']}: {verdict}  [{usage.get('in')} in / {usage.get('out')} out, "
              f"${usage.get('cost')}, {usage.get('finish')}]{name}")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifest", nargs="?", type=Path)
    ap.add_argument("--model", default=os.environ.get("CHAT_MODEL", DEFAULT_MODEL))
    ap.add_argument("--out", type=Path, default=Path("critique.json"))
    ap.add_argument("--compare", nargs=2, type=Path, metavar=("A.json", "B.json"))
    args = ap.parse_args()

    if args.compare:
        a, b = (json.loads(p.read_text()) for p in args.compare)
        diffs = disagreements(a, b)
        for d in diffs:
            print(d["name"])
            for x in d["diffs"]:
                print(f"  {x['requirement']}: {x['a']!r} vs {x['b']!r}")
        print(f"{len(diffs)} image(s) where the two critics disagree. Look at those yourself.")
        return
    if args.manifest is None:
        ap.error("manifest.json is required (or use --compare)")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; the critique is a billed vision call per image. Nothing checked.")
    # Imported here so the no-key path and the tests never need the SDK.
    from openrouter import OpenRouter

    results = critique_set(OpenRouter(api_key=key), args.model, args.manifest)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    bad = [r["name"] for r in results if not r["check"]["ok"] or r.get("text_matches") is False]
    cost = sum((r["usage"].get("cost") or 0) + (r.get("usage_text", {}).get("cost") or 0) for r in results)
    print(f"{len(results) - len(bad)}/{len(results)} images pass the code's check, ${cost:.5f}; written to {args.out}")


if __name__ == "__main__":
    main()
