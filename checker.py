"""Checks that a receipt's numbers add up. Plain code, no model. Never changes the receipt."""

TOLERANCE = 0.01


def money(x):
    return f"{x:.2f}"


def agree(a, b):
    return abs(round(a - b, 2)) <= TOLERANCE


def line_amount(item):
    return round(item.get("quantity", 1) * item["unit_price"], 2)


def check(receipt):
    """Return a list of problems in plain English; an empty list means the receipt adds up."""
    problems = []
    items = receipt.get("items", [])
    for item in items:
        if item.get("quantity", 1) < 1:
            problems.append("Item '{}' has quantity {}, below 1.".format(item.get("name"), item.get("quantity")))
    items_sum = round(sum(line_amount(i) for i in items), 2)
    subtotal = receipt.get("subtotal")
    discount = receipt.get("discount", 0) or 0
    tax = receipt.get("tax", 0) or 0
    total = receipt["total"]

    if total < 0:
        problems.append(f"Total is negative: {money(total)}.")

    if subtotal is None:
        computed = round(items_sum - discount + tax, 2)
        if not agree(computed, total):
            problems.append(f"Items {money(items_sum)} - discount {money(discount)} + tax {money(tax)} = {money(computed)}, but the total is {money(total)} (off by {money(abs(computed - total))}).")
        return problems

    if not agree(items_sum, subtotal):
        problems.append(f"Items add up to {money(items_sum)}, but the subtotal is {money(subtotal)} (off by {money(abs(items_sum - subtotal))}).")
    computed = round(subtotal - discount + tax, 2)
    if not agree(computed, total):
        problems.append(f"Subtotal {money(subtotal)} - discount {money(discount)} + tax {money(tax)} = {money(computed)}, but the total is {money(total)} (off by {money(abs(computed - total))}).")
    return problems
