# DevFolio

DevFolio is a single-owner portfolio and blog. The backend is a Django REST
Framework API; the separately versioned frontend is a React/Vite application.
Visitors can view published content, like posts, leave comments, and send
contact messages. The portfolio owner can manage content and moderate
submissions.

## Architecture

```text
Browser
  React 19 + Vite
  React Router       public pages and protected owner dashboard
  TanStack Query     API-backed server state
  Axios              API transport, JWT and visitor headers
       |
       | JSON requests to /api/ (CORS enabled)
       v
Django 5 + Django REST Framework
  config/             settings, root URLs, WSGI entry point
  portfolio/          models, serializers, permissions, viewsets and signals
  PostgreSQL          production database via DATABASE_URL
  SQLite              local fallback when DATABASE_URL is unset
```

The public profile endpoint returns one profile object. Public post querysets
contain published posts only; the authenticated superuser can manage drafts.
Static files are collected to `staticfiles/` and served through WhiteNoise.

## API endpoints

All API paths are prefixed with `/api/` and use trailing slashes.

| Area | Endpoints | Access |
|---|---|---|
| Authentication | `POST auth/login/`, `POST auth/refresh/`, `GET auth/me/`, `POST auth/logout/`, `POST auth/change-password/` | Owner |
| Profile | `GET profile/`, `PATCH profile/` | Public read; owner write |
| Portfolio data | `GET/POST/PATCH/DELETE skills/`, `experiences/`, `education/`, `projects/`, `categories/`, `tags/` | Public read; owner write |
| Posts | `GET/POST posts/`, `GET/PATCH/DELETE posts/{slug}/` | Published public; owner manages all |
| Post engagement | `POST posts/{slug}/like/`, `GET/POST posts/{slug}/comments/` | Public |
| Comment moderation | `GET comments/`, `POST comments/{id}/approval/`, `POST comments/replies/` | Owner |
| Contact | `POST contact/`, `GET contact/`, `PATCH contact/{id}/read-state/` | Public submission; owner inbox |
| Dashboard | `GET dashboard/stats/` | Owner |
| Django admin | `/admin/` | Django staff |

List endpoints are paginated. Search, filtering, and ordering are available
where configured by the viewset. Comment submissions default to pending; public
comment reads include approved comments and approved one-level replies. Published
posts require a category and at least 300 words.

## Authentication and visitor identity

The owner signs in through `POST /api/auth/login/` and receives SimpleJWT access
and refresh tokens. Send protected requests with
`Authorization: Bearer <access-token>`. Refresh an access token through
`POST /api/auth/refresh/`; use `POST /api/auth/logout/` to blacklist a refresh
token. Only an authenticated superuser is treated as the portfolio owner. There
is no public registration endpoint.

The frontend creates a UUID visitor ID and stores it in browser local storage.
It sends this value as `X-Visitor-Id` on API requests. Post likes are unique per
post and visitor; the header also supports the API's view-count cooldown.
Browser local storage is accessible to JavaScript running on the site; use
standard XSS protections and never store a token in source code.

## Environment variables

Copy `.env.example` to `.env` for local backend development. Values in the
example are placeholders and must be replaced where appropriate.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django signing secret; use a private random value outside local development |
| `DEBUG` | Enables Django debug behavior; disable in production |
| `ALLOWED_HOSTS` | Comma-separated accepted hostnames |
| `DATABASE_URL` | PostgreSQL connection URL; when unset, settings fall back to `db.sqlite3` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins permitted to call the API |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins for Django CSRF checks |
| `RENDER` | Set by Render to enable production defaults |
| `RENDER_EXTERNAL_HOSTNAME` | Render-provided service hostname, added to allowed hosts |

The frontend has its own `VITE_API_BASE_URL`, configured in
`frontend/.env`; its local example points to `http://127.0.0.1:8000/api/`.
Frontend `VITE_` variables are embedded in the browser bundle and must not
contain secrets.

## Local development

### Backend

From the repository root, using Windows PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Set a private `SECRET_KEY` and local CORS origins in `.env`. For a local
PostgreSQL database, set `DATABASE_URL`; otherwise SQLite is used.

### Frontend

In another terminal:

```powershell
Set-Location frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to the backend API root, including `/api/`. The Vite
production bundle is generated in `frontend/dist`.

## Demo data

After migrations, create the baseline profile, categories, skills, and featured
project with:

```powershell
python manage.py seed_demo
```

The command uses `get_or_create`, so rerunning it does not overwrite existing
records. The optional comment demo is separate and deliberately defaults to a
read-only preview:

```powershell
python manage.py seed_demo_comments
```

Only run `python manage.py seed_demo_comments --apply` after reviewing and
approving its clearly labeled sample content. Do not seed demo comments in
production.

## Tests and checks

Run backend checks from the repository root:

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

Build the frontend:

```powershell
Set-Location frontend
npm run build
```

The backend tests use Django's isolated test database. No automated frontend
test script is currently configured.

## Render deployment

The root `render.yaml` defines a Python web service. Render runs `build.sh`,
which installs requirements, collects static files, applies migrations, and
creates baseline demo data. Configure `DATABASE_URL` and `SECRET_KEY` as
Render environment variables; both are marked `sync: false` in the Blueprint.
The service starts with Gunicorn at `config.wsgi:application`.

The React frontend is deployed separately. Set its production
`VITE_API_BASE_URL` to the Render API root, for example
`https://<your-render-service>.onrender.com/api/`, then deploy the frontend
from its repository using Vercel or another static host.

## Postman

Import `docs/postman/DevFolio.postman_collection.json` and optionally
`docs/postman/DevFolio.postman_environment.json`. Set the base URL and keep
obtained JWTs in a local Postman environment. Collection examples use
placeholders, not credentials. Run write requests against a local or test
database.
