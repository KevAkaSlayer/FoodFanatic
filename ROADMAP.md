# FoodFanatic restaurant management roadmap

## Product direction

FoodFanatic should grow from a customer ordering demo into a dependable restaurant
operations platform. Each phase below has a narrow goal and explicit completion
criteria so the system can remain deployable while it evolves.

## Phase 1 — Safety and order integrity (complete)

Goal: make the current menu, cart, account, review, and ordering flows reliable.

- Move secrets and deployment settings to environment variables.
- Upgrade to the supported Django 5.2 LTS release line.
- Store immutable order-item snapshots instead of references to temporary carts.
- Make checkout atomic and preserve the price charged at checkout.
- Enforce user ownership on carts, orders, and profile updates.
- Use POST + CSRF protection for cart, checkout, and logout mutations.
- Validate menu prices, discounts, quantities, dates, emails, and review ratings.
- Permit reviews only after a non-cancelled purchase, one review per item.
- Add automated tests for authorization, pricing, checkout, and record retention.
- Improve admin screens for day-to-day menu and order operations.

Acceptance: checks and tests pass; placing an order clears the cart without losing
the order lines; one user cannot mutate or view another user's records.

Status: met. `manage.py check` reports no issues and the suite passes. A cart
price is treated as a quote — checkout re-reads the live price and returns the
customer to the cart to re-confirm whenever it moved, so an expired discount is
never charged.

## Phase 2 — Money model, staff roles, and core operations

Goal: support the work happening inside a restaurant, on a financial schema that
later phases extend rather than rewrite.

Land the full order money breakdown here, in one migration, even though the
values that fill it arrive in Phase 3. `Order` currently stores only
`total_amount`; splitting subtotal, discount, tax, service charge, and tip across
two phases would migrate financial history twice.

- Order money breakdown: subtotal, discount, tax, service charge, tip, and total
  as separate `Decimal` columns, with a check that the parts sum to the total.
- Restaurant/branch, service hours, tax profile, and currency settings.
- Dine-in, pickup, and delivery order types.
- Tables, seating, reservations, wait-list, and guest counts.
- Kitchen tickets with received, preparing, ready, served, and cancelled states.
- Menu modifiers (size, add-ons, cooking preference) and allergen information.
- Staff roles for owner, manager, cashier, server, kitchen, and delivery.
- Append-only audit log covering every staff and financial action, shipped in the
  same phase as the roles it records.
- Internal JSON endpoints backing the staff screens.

Decide before starting: whether kitchen tickets replace the existing
`Order.Status` values (`PENDING`, `PREPARING`, `READY`, `COMPLETED`, `CANCELLED`)
or track preparation separately from the customer-facing order state. The two
overlap, and resolving it mid-migration is expensive.

Acceptance: staff can take and fulfill an order from arrival to completion without
using Django admin or editing database records, and every privileged action they
take is recorded in the audit log.

## Phase 3 — Payments and customer experience

Goal: make ordering and payment production-ready. This precedes inventory because
a restaurant cannot take money correctly without it, and nothing here depends on
food-cost tracking.

- Populate the Phase 2 money columns: tax, service charge, tips, and coupons.
- Refunds, voids, and split payments.
- Payment-provider integration using idempotent webhooks.
- Guest checkout, saved addresses, order tracking, and receipts.
- Loyalty points, customer notes, promotions, and notification preferences.
- Versioned public REST API for web and mobile clients.

Acceptance: payment state is reconciled independently from order state and retries
cannot double-charge or duplicate an order.

## Phase 4 — Inventory and purchasing

Goal: connect sales to food cost and stock.

- Ingredients, recipes, units, suppliers, and purchase orders.
- Stock receipts, consumption, waste, adjustments, and low-stock alerts.
- Automatic ingredient deduction when kitchen preparation begins.
- Cost-of-goods and menu-margin reporting.
- Branch-level inventory and stock transfers.

Acceptance: stock movement is auditable and each sold item has a reproducible food
cost.

## Phase 5 — Reporting, governance, and scale

Goal: give operators control and production visibility.

- Shift opening/closing, cash drawer reconciliation, and daily sales summaries.
- Sales, tax, discount, void, staff performance, and inventory reports.
- Audit-log search and retention policy, building on the Phase 2 log.
- Background jobs for email, exports, and integrations.
- Verified backup restores, error tracking, metrics, and alerts.
- Accessibility, localization, multi-currency, performance, and load testing.

PostgreSQL production deployment is already done — see `docs/PRODUCTION.md`.

Acceptance: management can reconcile a business day, investigate every sensitive
change, restore backups, and monitor service health.

## Cross-cutting rules

- Financial values are `Decimal` snapshots, never floating-point calculations.
- Customer and staff access follows least privilege.
- Every state-changing web action is authenticated, authorized, and CSRF protected.
- Database constraints back up application validation.
- Migrations preserve existing data and include a rollback/recovery plan.
- Each phase ships with tests and operational documentation.
