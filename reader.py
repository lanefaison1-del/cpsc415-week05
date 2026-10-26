"""Reads a receipt image with a vision model and returns it as a dictionary.

Settings come from the environment: OPENROUTER_API_KEY, CHAT_BASE_URL, CHAT_MODEL,
CHAT_REASONING (set to "off" to send reasoning: {enabled: false}).
"""
import base64
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from checker import check

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "minimax/minimax-m3"
TIMEOUT = 60

PROMPT = """Read this receipt and reply with one JSON object and nothing else, with exactly these fields:
{"merchant": string, "date": "YYYY-MM-DD" or null, "items": [{"name": string, "quantity": number, "unit_price": number}],
 "subtotal": number or null, "discount": number, "tax": number, "total": number}
Rules:
- merchant is the store name as printed at the top.
- date is null if the year is not printed on the receipt. A two-digit year such as 26 means 2026.
- Each printed item line is one item. If a line says "3 x Gel pen @ 0.89", quantity is 3 and unit_price is 0.89.
- subtotal is null if no subtotal line is printed. discount and tax are 0 if not printed.
- discount is the amount taken off, as a positive number.
- Money is a plain number with no currency sign."""


class ParseError(ValueError):
    """The model's reply could not be turned into a receipt."""


def to_number(value, field):
    if isinstance(value, bool):
        raise ParseError("{} is not a number: {!r}".format(field, value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            pass
    raise ParseError("{} is not a number: {!r}".format(field, value))


def clean_date(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.date.fromisoformat(value.strip()).isoformat()
    except ValueError:
        return None


def parse_reply(text):
    """Turn a model reply into a receipt dictionary, or raise ParseError."""
    if not text or "{" not in text or "}" not in text:
        raise ParseError("reply is not JSON: {!r}".format((text or "")[:80]))
    try:
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    except json.JSONDecodeError as e:
        raise ParseError("reply is not JSON: {}".format(e))
    if not isinstance(data, dict):
        raise ParseError("reply is not a JSON object")
    for field in ("merchant", "items", "total"):
        if data.get(field) is None:
            raise ParseError("reply is missing {}".format(field))
    if not isinstance(data["items"], list):
        raise ParseError("items is not a list")
    items = []
    for i, item in enumerate(data["items"]):
        if not isinstance(item, dict) or item.get("unit_price") is None:
            raise ParseError("item {} is missing unit_price".format(i + 1))
        quantity = item.get("quantity")
        items.append({
            "name": str(item.get("name", "")),
            "quantity": 1.0 if quantity is None else to_number(quantity, "item {} quantity".format(i + 1)),
            "unit_price": to_number(item["unit_price"], "item {} unit_price".format(i + 1)),
        })
    subtotal = data.get("subtotal")
    return {
        "merchant": str(data["merchant"]).strip(),
        "date": clean_date(data.get("date")),
        "items": items,
        "subtotal": None if subtotal is None else to_number(subtotal, "subtotal"),
        "discount": abs(to_number(data.get("discount") or 0, "discount")),
        "tax": to_number(data.get("tax") or 0, "tax"),
        "total": to_number(data["total"], "total"),
    }


def build_request(path):
    mime = "image/png" if str(path).lower().endswith(".png") else "image/jpeg"
    img = base64.b64encode(Path(path).read_bytes()).decode()
    body = {
        "model": os.environ.get("CHAT_MODEL", DEFAULT_MODEL),
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": "data:{};base64,{}".format(mime, img)}},
        ]}],
    }
    if os.environ.get("CHAT_REASONING", "").lower() == "off":
        body["reasoning"] = {"enabled": False}
    return body


def read_receipt(path):
    """Return (receipt or None, usage). usage has prompt_tokens, completion_tokens, finish_reason, error."""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "finish_reason": None, "error": None, "raw": ""}
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        usage["error"] = "OPENROUTER_API_KEY is not set"
        return None, usage
    url = os.environ.get("CHAT_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(build_request(path)).encode(), headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            reply = json.load(resp)
    except urllib.error.HTTPError as e:
        usage["error"] = "HTTP {}".format(e.code)
        return None, usage
    except (urllib.error.URLError, OSError, ValueError) as e:
        usage["error"] = "request failed: {}".format(e)
        return None, usage
    u = reply.get("usage") or {}
    usage["prompt_tokens"] = u.get("prompt_tokens", 0)
    usage["completion_tokens"] = u.get("completion_tokens", 0)
    choice = (reply.get("choices") or [{}])[0]
    usage["finish_reason"] = choice.get("finish_reason")
    content = (choice.get("message") or {}).get("content") or ""
    usage["raw"] = content
    try:
        return parse_reply(content), usage
    except ParseError as e:
        usage["error"] = "failed read ({}): {}".format(usage["finish_reason"], e)
        return None, usage


def main(argv):
    if len(argv) != 2:
        print("usage: python reader.py path/to/receipt.png")
        return 2
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set.")
        return 1
    receipt, usage = read_receipt(argv[1])
    print("model: {}  tokens in {}, out {}, finish {}".format(
        os.environ.get("CHAT_MODEL", DEFAULT_MODEL), usage["prompt_tokens"],
        usage["completion_tokens"], usage["finish_reason"]))
    if receipt is None:
        print(usage["error"])
        return 1
    print(json.dumps(receipt, indent=2))
    problems = check(receipt)
    print("problems: none" if not problems else "problems:\n- " + "\n- ".join(problems))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
