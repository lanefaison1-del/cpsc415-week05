# Intent: receipts to data

## Goal

Given one photograph of a receipt, produce the receipt as structured data (merchant, date, line items with quantity and unit price, subtotal, discount, tax, total) and then check, in ordinary code, that the numbers on the receipt add up. The program reports any problem it finds; it never changes the numbers to make them agree.

## Who it is for

Me, and anyone who wants to log a stack of paper receipts without typing them in. Today that means reading each receipt and keying it into a spreadsheet by hand, and trusting that I copied it right.

## Constraints

- One image in, one JSON result plus a list of problems out.
- A vision model reads the image; plain code does every arithmetic check. The model's own claim that the numbers add up is never trusted.
- Two models compared: `minimax/minimax-m3` and `xiaomi/mimo-v2.6-flash`, through OpenRouter. The key comes from the environment, never from the repository.
- Cost: well under a cent per receipt; the whole lab, both models and my own receipts included, under $0.25.
- Due Monday, October 26, 2026.

## Not in scope

- Fixing a receipt that does not add up, or guessing a missing value.
- Card numbers, cardholder names, payment method, or the store address.
- More than one receipt per image, PDFs, or multi-page receipts.
- Currency conversion: all amounts are dollars.

## Success looks like

- The five course receipts come back with the right merchant, date, number of items and total, and the checker reports no problems on any of them.
- A receipt where the line items do not add up to the subtotal, or the subtotal, discount and tax do not produce the total, is reported with both numbers and the difference.
- A receipt with no year printed on it comes back with the date as null, not with a guessed year.

## Decisions from the interview

- An item is one printed line, so "3 x Gel pen @ 0.89" is one item with quantity 3 and unit price 0.89.
- A discount is recorded as a positive amount that is subtracted, whatever sign the receipt prints it with.
- Amounts agree when they are within one cent.
- A receipt with no subtotal line (a bake sale) is checked items-to-total directly.

## Open questions

None.

**Approved by:** Lane Faison, October 26, 2026
