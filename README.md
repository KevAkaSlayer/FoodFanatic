# FoodFanatic

FoodFanatic is a Django restaurant ordering and management application. Phase 1
provides a reliable customer-facing foundation: menu browsing, dated discounts,
accounts with email verification, cart management, atomic checkout, persistent
order history, purchase-gated reviews, and improved Django admin operations.

See [ROADMAP.md](ROADMAP.md) for the phase-by-phase path to tables, reservations,
kitchen tickets, staff roles, inventory, payments, reporting, and production
operations.

Production database setup and catalog bootstrapping are documented in
[docs/PRODUCTION.md](docs/PRODUCTION.md).

Vercel deployments require a persistent Postgres integration that supplies
`DATABASE_URL` or Supabase's `POSTGRES_URL`. The included Vercel build hook
applies Django migrations after the database is connected.

## Local setup (PowerShell)

The project targets Python 3.10–3.14 and Django 5.2 LTS.

```powershell
.\run.ps1
```

`run.ps1` creates the virtual environment, installs dependencies, copies
`.env.example` to `.env`, applies migrations, and starts the development server
on http://127.0.0.1:8000/. Each setup step is skipped once it is already done, so
the same command works for the first run and every run after it.

It also forwards anything else to `manage.py`, with a few short aliases:

```powershell
.\run.ps1 seed        # load the 20 demo menu items
.\run.ps1 admin       # create a superuser for /admin/
.\run.ps1 test        # run the test suite
.\run.ps1 check       # run system checks
```

To run the underlying commands directly instead:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_menu
.\.venv\Scripts\python.exe manage.py runserver
```

Set a unique `SECRET_KEY` in `.env`. Development email uses Django's console
backend, so verification links are printed in the terminal instead of being sent.
To use SMTP, set the email variables shown in `.env.example`.

## Verification

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m pip check
```

Production configuration should set `DEBUG=False`, a strong `SECRET_KEY`, explicit
`ALLOWED_HOSTS`, the public HTTPS origin in `CSRF_TRUSTED_ORIGINS`, a PostgreSQL
`DATABASE_URL`, and the secure transport values from `.env.example`. Validate it
before release with:

```powershell
.\.venv\Scripts\python.exe manage.py check --deploy
```

## Important data behavior

- A cart row is temporary. Checkout writes independent `OrderItem` snapshots with
  product name, quantity, and charged unit price before clearing the cart.
- Order totals and line totals use decimal arithmetic.
- Deleting a menu item does not delete historical order lines.
- Mutating browser actions use authenticated POST requests with CSRF protection.
- A customer can review only an item present in one of their non-cancelled orders.

The Phase 1 migration was applied to the local SQLite database. Both that
database and its `.backups/db-before-phase1.sqlite3` backup are git-ignored and
remain on the developer machine.
