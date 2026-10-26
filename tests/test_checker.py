"""Checker tests: hand-written receipts, no model, no key."""
from checker import check


def receipt(**overrides):
    base = {
        "merchant": "Mather Dining Hall",
        "date": "2026-10-02",
        "items": [
            {"name": "Chicken wrap", "quantity": 1, "unit_price": 7.49},
            {"name": "Side salad", "quantity": 1, "unit_price": 3.25},
            {"name": "Iced tea", "quantity": 1, "unit_price": 2.10},
        ],
        "subtotal": 12.84,
        "discount": 0,
        "tax": 0.82,
        "total": 13.66,
    }
    base.update(overrides)
    return base


def test_receipt_that_adds_up_has_no_problems():
    assert check(receipt()) == []


def test_wrong_total_is_reported_with_both_numbers():
    problems = check(receipt(total=13.96))
    assert len(problems) == 1
    assert "13.66" in problems[0] and "13.96" in problems[0] and "0.30" in problems[0]


def test_items_not_adding_to_subtotal_is_reported():
    problems = check(receipt(subtotal=12.94, total=13.76))
    assert len(problems) == 1
    assert "12.84" in problems[0] and "12.94" in problems[0]


def test_discount_is_subtracted():
    r = receipt(
        items=[
            {"name": "Latte 12oz", "quantity": 1, "unit_price": 4.75},
            {"name": "Croissant", "quantity": 1, "unit_price": 3.50},
            {"name": "Americano", "quantity": 1, "unit_price": 3.25},
        ],
        subtotal=11.50, discount=1.15, tax=0.66, total=11.01,
    )
    assert check(r) == []


def test_quantity_times_unit_price():
    r = receipt(
        items=[
            {"name": "Blue book", "quantity": 2, "unit_price": 1.25},
            {"name": "Gel pen", "quantity": 3, "unit_price": 0.89},
        ],
        subtotal=5.17, tax=0, total=5.17,
    )
    assert check(r) == []


def test_no_subtotal_checks_items_against_total():
    r = receipt(
        items=[
            {"name": "Brownie", "quantity": 1, "unit_price": 2.00},
            {"name": "Cookies", "quantity": 3, "unit_price": 1.00},
            {"name": "Lemonade", "quantity": 1, "unit_price": 1.50},
        ],
        subtotal=None, tax=0, total=6.50,
    )
    assert check(r) == []
    bad = dict(r, total=7.50)
    problems = check(bad)
    assert len(problems) == 1 and "6.50" in problems[0] and "7.50" in problems[0]


def test_one_cent_is_within_tolerance():
    assert check(receipt(total=13.67)) == []


def test_two_cents_is_not():
    assert len(check(receipt(total=13.68))) == 1


def test_negative_total_and_bad_quantity_are_reported():
    r = receipt(items=[{"name": "x", "quantity": 0, "unit_price": 1.0}],
                subtotal=0, tax=0, total=-1.0)
    problems = check(r)
    assert any("quantity" in p for p in problems)
    assert any("negative" in p for p in problems)


def test_checker_does_not_change_the_receipt():
    r = receipt(total=13.96)
    before = repr(r)
    check(r)
    assert repr(r) == before
