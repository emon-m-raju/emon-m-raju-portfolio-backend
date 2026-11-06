# DevFolio

A single-owner developer portfolio with a Django REST Framework API and React/Vite frontend. Public visitors can browse portfolio and blog content, leave comments, and send contact messages. The authenticated portfolio owner can manage content, moderate comments, and handle messages.

## Technology

- Backend: Python, Django, Django REST Framework, SimpleJWT, django-filter, SQLite, Pillow, django-cors-headers
- Frontend: React, Vite, React Router, TanStack Query, Axios
- API: JSON over HTTP; media files are served locally by Django in development

## Project layout

```text
config/                 Django settings and URL configuration
portfolio/              Models, serializers, permissions, views, tests, admin
portfolio/migrations/   Database migrations
portfolio/management/   Safe demo-comment preview/seed command
frontend/src/api/        Shared Axios API client and API functions
frontend/src/dashboard/  Owner dashboard pages
frontend/src/sections/   Public portfolio sections
docs/                    Submission checklist, recording script, Postman files
```

## Local setup

### Backend

Use Python supported by the installed Django release. From the project root:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a private, random `SECRET_KEY` and appropriate `DEBUG`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` values in your local `.env`. Never commit `.env` or put credentials in the Postman collection. Apply existing migrations and create an owner account:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

No schema change is required for the implemented features. Do not generate migrations unless a future model change requires one.

### Frontend

In another terminal:

```powershell
Set-Location frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to the backend API root (the template uses `http://127.0.0.1:8000/api/`). `npm run build` creates the production bundle in `frontend/dist`.

## API overview

All paths below are relative to `/api/`, except the Django admin.

| Area | Endpoint(s) | Access |
|---|---|---|
| Authentication | `POST auth/login/`, `POST auth/refresh/`, `GET auth/me/`, `POST auth/logout/`, `POST auth/change-password/` | Owner login/JWT |
| Profile | `GET profile/`, owner `PATCH profile/` | Public read; owner write |
| Portfolio data | `GET/POST/PATCH/DELETE skills/`, `experiences/`, `education/`, `projects/`, `categories/`, `tags/` | Public read; owner write |
| Posts | `GET/POST/PATCH/DELETE posts/`, `GET posts/{slug}/`, `POST posts/{slug}/like/`, `GET/POST posts/{slug}/comments/` | Published public; owner manages all |
| Comment moderation | `GET comments/`, `POST comments/{id}/approval/`, `POST comments/replies/` | Owner only |
| Contact messages | `POST contact/` (public); owner `GET contact/` and `PATCH contact/{id}/read-state/` | Public submission; owner inbox |
| Dashboard | `GET dashboard/stats/` | Owner only |
| Admin | `/admin/` | Django staff |

List APIs use DRF pagination. Supported list search/filter/order parameters are exposed by the viewsets (for example `search`, `ordering`, `is_read`, `is_approved`, `category`, and `is_featured`). Public post lists contain published posts only; owners can request `?status=DRAFT` or `?status=all`. Published posts require a category and at least 300 words. Comment replies are owner-created and approved; public comment responses omit commenter email.

Authenticate owner requests with `Authorization: Bearer <access_token>`. Refresh tokens through `auth/refresh/`; use `auth/logout/` to blacklist a refresh token. The frontend keeps the shared Axios client as its API transport and TanStack Query for server-state operations.

## Tests and checks

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
Set-Location frontend
npm run build
```

The backend tests use Django's isolated test database. The frontend currently has a production build command but no dedicated automated frontend test script. See [docs/FINAL_SUBMISSION_CHECKLIST.md](./docs/FINAL_SUBMISSION_CHECKLIST.md) for verified project thresholds and remaining manual actions.

## Postman

Import [docs/postman/DevFolio.postman_collection.json](./docs/postman/DevFolio.postman_collection.json) and optionally [docs/postman/DevFolio.postman_environment.json](./docs/postman/DevFolio.postman_environment.json). Set `base_url`, obtain JWT tokens using the login request, and place the tokens only in a local Postman environment. Collection examples use placeholders, not real credentials. Public contact/comment submissions create data; use a local/test database for write requests.

## Demo comment seed safety

`python manage.py seed_demo_comments` previews five clearly labeled fictional comments and one fictional owner reply. It does not write by default. Review the exact preview and obtain explicit approval before running `python manage.py seed_demo_comments --apply`. The command does not edit existing rows and aborts on a conflicting pre-existing demo row. Do not run it against production.

## Repository and deployment

No Git remote or deployment URL has been verified for this workspace. Add only links that have been independently confirmed.
