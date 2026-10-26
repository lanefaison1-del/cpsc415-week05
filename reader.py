"""Reads a receipt image with a vision model and returns it as a dictionary."""
import datetime
import json

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
