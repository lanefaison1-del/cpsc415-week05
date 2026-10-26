"""Checks that a receipt's numbers add up. Plain code, no model. Never changes the receipt."""

TOLERANCE = 0.01


def money(x):
    return "{:.2f}".format(x)


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
        problems.append("Total is negative: {}.".format(money(total)))

    if subtotal is None:
        computed = round(items_sum - discount + tax, 2)
        if not agree(computed, total):
            problems.append("Items {} - discount {} + tax {} = {}, but the total is {} (off by {}).".format(
                money(items_sum), money(discount), money(tax), money(computed), money(total),
                money(abs(computed - total))))
        return problems

    if not agree(items_sum, subtotal):
        problems.append("Items add up to {}, but the subtotal is {} (off by {}).".format(
            money(items_sum), money(subtotal), money(abs(items_sum - subtotal))))
    computed = round(subtotal - discount + tax, 2)
    if not agree(computed, total):
        problems.append("Subtotal {} - discount {} + tax {} = {}, but the total is {} (off by {}).".format(
            money(subtotal), money(discount), money(tax), money(computed), money(total),
            money(abs(computed - total))))
    return problems
