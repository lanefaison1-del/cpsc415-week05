"""Parser tests: hand-written model replies, no model, no key."""
import pytest

from reader import ParseError, parse_reply

CLEAN = ('{"merchant": "Long Walk Coffee", "date": "2026-10-06", "items": ['
         '{"name": "Latte 12oz", "quantity": 1, "unit_price": 4.75}], '
         '"subtotal": 4.75, "discount": 0, "tax": 0.30, "total": 5.05}')


def test_clean_json():
    r = parse_reply(CLEAN)
    assert r["merchant"] == "Long Walk Coffee"
    assert r["total"] == 5.05
    assert r["items"][0]["quantity"] == 1


def test_json_inside_prose():
    r = parse_reply("Sure! Here is the receipt:\n" + CLEAN + "\nLet me know if you need more.")
    assert r["total"] == 5.05


def test_json_in_code_fence():
    r = parse_reply("```json\n" + CLEAN + "\n```")
    assert r["merchant"] == "Long Walk Coffee"


@pytest.mark.parametrize("reply", ["", "   ", "I cannot read this image.", "{not json at all}"])
def test_not_json_is_a_failed_read(reply):
    with pytest.raises(ParseError):
        parse_reply(reply)


def test_missing_total_names_the_field():
    with pytest.raises(ParseError, match="total"):
        parse_reply('{"merchant": "X", "items": []}')


def test_non_numeric_amount_is_a_failed_read():
    with pytest.raises(ParseError, match="tax"):
        parse_reply('{"merchant": "X", "items": [], "tax": "about a dollar", "total": 1}')


def test_negative_discount_becomes_positive():
    r = parse_reply(CLEAN.replace('"discount": 0', '"discount": -1.15'))
    assert r["discount"] == 1.15


def test_missing_discount_tax_and_quantity_default():
    r = parse_reply('{"merchant": "X", "items": [{"name": "a", "unit_price": 2}], "total": 2}')
    assert r["discount"] == 0 and r["tax"] == 0 and r["subtotal"] is None
    assert r["items"][0]["quantity"] == 1


@pytest.mark.parametrize("date", [None, "", "10-03", "Oct 3", "2026-13-03", "unknown"])
def test_date_without_a_year_is_null(date):
    r = parse_reply(CLEAN.replace('"2026-10-06"', "null" if date is None else f'"{date}"'))
    assert r["date"] is None


def test_amount_given_as_string_with_dollar_sign():
    r = parse_reply(CLEAN.replace('"total": 5.05', '"total": "$5.05"'))
    assert r["total"] == 5.05
