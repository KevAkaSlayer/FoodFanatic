# Production database and catalog

Production data belongs in a persistent database, not in the Git repository.
FoodFanatic supports PostgreSQL through the `DATABASE_URL` environment variable.

## Vercel project settings

FoodFanatic includes `vercel.json` with the Django framework preset. In the
Vercel project:

- Keep **Root Directory** at the repository root.
- Keep **Build Command** and **Output Directory** overrides empty so Vercel's
  Django adapter can detect `manage.py`, the WSGI application, templates, and
  static files.
- Set the variables below for both Production and Preview where appropriate.
- Connect persistent PostgreSQL before deploying. Serverless SQLite is not
  supported because function filesystems are ephemeral.

## First deployment

1. Provision a managed PostgreSQL database with automated backups. On Vercel,
   open the project's **Storage** tab, create a Supabase or Neon Postgres
   integration, and connect it to the `food-fanatic` project. The application
   accepts the pooled connection string as either `DATABASE_URL` or the
   `POSTGRES_URL` variable injected by Supabase's Vercel integration.
2. Set the production environment variables:

   ```text
   DEBUG=False
   SECRET_KEY=<long-random-secret>
   ALLOWED_HOSTS=.vercel.app,restaurant.example.com
   CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://restaurant.example.com
   DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
   SUPABASE_STORAGE_BUCKET=foodfanatic-media
   SECURE_SSL_REDIRECT=True
   SECURE_HSTS_SECONDS=31536000
   ```

3. Install dependencies and build static assets:

   ```shell
   python -m pip install -r requirements.txt
   python manage.py collectstatic --noinput
   ```

4. Create/update the schema:

   ```shell
   python manage.py migrate
   ```

   Vercel also runs this command on each deployment through
   `[tool.vercel.scripts]` in `pyproject.toml`. Keep the database URL scoped to
   Production unless Preview uses an isolated database branch.

5. Import the non-sensitive starter catalog:

   ```shell
   python manage.py seed_menu
   ```

   The command is idempotent: rerunning it creates only missing records. Use
   `--update-existing` only when the packaged catalog should overwrite matching
   descriptions, prices, categories, availability, and discount configuration.
   Starter images are copied into the configured media storage.

   On Vercel, the build hook automatically runs this seed with `--if-empty`
   after migrations. It adds the starter menu only to a brand-new empty
   database and never overwrites an existing restaurant menu.

6. Create the first operator account:

   ```shell
   python manage.py createsuperuser
   ```

For Vercel, migrations and the one-time empty-menu seed run during the build
after the database integration has injected `DATABASE_URL` or `POSTGRES_URL`.
Run the superuser command from a trusted workstation or CI job with the
production database URL. Do not store that URL in Git.

Supabase's Vercel integration may append a `supa` routing marker to
`POSTGRES_URL`. FoodFanatic removes that provider metadata before passing the
remaining connection options to psycopg. Transaction-pooler URLs on port 6543
also disable prepared statements and server-side cursors.

When using `vercel env run`, the injected `DATABASE_URL` or `POSTGRES_URL`
takes precedence over a developer's local `.env` file.

## Later deployments

Run `python manage.py migrate` during every deployment. Migrations modify the
schema while the managed PostgreSQL service retains customers, orders, reviews,
and restaurant configuration.

Do not run `flush`, delete the database, or run `seed_menu --update-existing`
automatically during deployments.

## Media persistence

The database stores image paths, while the image files live in media storage.
On Vercel, FoodFanatic uses the connected Supabase project's Storage service:

- The deployment creates a public `foodfanatic-media` bucket when necessary.
- Packaged menu photos are safely filled in only for existing menu items with
  no image; staff-created images and menu details are not overwritten.
- The bucket is public because restaurant menu images need direct browser URLs.
  `SUPABASE_SERVICE_ROLE_KEY` is never sent to the browser and must remain a
  sensitive Vercel variable.

### Image sizes

Uploads are downscaled and re-encoded before they reach storage, so a
multi-megapixel camera original is not served to a browser that renders it in a
200 pixel card. `IMAGE_MAX_WIDTH` (default 1200) and `IMAGE_QUALITY` (default
82) tune this; the file format is preserved so stored names stay accurate.

Images stored before this existed are not touched automatically. Rewrite them
once, from a trusted workstation holding the production database and Supabase
variables:

```shell
python manage.py compress_menu_images --dry-run   # report the savings
python manage.py compress_menu_images             # apply them
```

Each rewritten image is saved under a new name and the old object is deleted,
because uploads carry a one-year `cache-control` and reusing the path would let
caches keep serving the original. The command only rewrites an image that gets
at least 10% smaller (`--min-saving`), so repeat runs are no-ops rather than
repeated re-encodings.

The Supabase Vercel integration already provides `SUPABASE_URL` and
`SUPABASE_SERVICE_ROLE_KEY` for Production and Preview. Add
`SUPABASE_STORAGE_BUCKET=foodfanatic-media` as a non-sensitive project variable
if you want to use a different bucket name, then redeploy. Local development
continues to use `MEDIA_ROOT` unless both Supabase variables are set.

## Backups and local development

- Enable daily PostgreSQL backups and test restores periodically.
- Keep `.env`, SQLite databases, production dumps, and media uploads out of Git.
- Local development continues to use the git-ignored `db.sqlite3`.
- To restore the packaged starter catalog locally, run `python manage.py seed_menu`.
