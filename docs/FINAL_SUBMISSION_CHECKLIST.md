# Final assignment checklist

Status reflects the existing local database and the automated checks run for this audit.

| Requirement | Status | Evidence / next action |
|---|---|---|
| At least 10 skills across 3 categories | PASS | 16 skills across 3 categories. |
| At least 2 combined education/experience entries | FAIL | 1 education entry and 0 experience entries. Add only a genuine entry supplied by the owner; do not invent experience. |
| At least 3 real projects | PASS | 5 existing projects. |
| 5 posts: 4 published articles (300+ words) and 1 draft | PASS | 5 posts: 4 published (450, 420, 457, 451 words) and 1 draft (449 words). API validation now requires 300 words for published posts. |
| At least 3 categories and 6 tags | PASS | 3 categories and 9 tags. |
| 5 comments, 2 unapproved, and 1 reply | PASS | With explicit owner approval, seeded 5 clearly labeled `[DEMO COMMENT]` parents (3 approved, 2 pending) and 1 approved fictional reply. Verified totals: 6 comments, 5 top-level, 1 reply, 4 approved including the reply, 2 pending. |
| At least 2 contact messages | PASS | 2 existing messages; preserved. |
| Public pages and owner management routes | PASS | Public portfolio and owner routes for profile, skills, projects, blog, categories, tags, comments, and messages exist. |
| JWT and owner-only API permissions | PASS | Backend uses JWT and owner/superuser permissions; tests cover representative protected APIs. |
| Shared Axios and React Query | PASS | Public and owner API integrations use the shared Axios client; React Query is used for fetching/mutations. |
| Loading, error, empty, retry, and validation behavior | PASS | Present in API-backed public and owner flows; covered in targeted review and backend validation tests. |
| Backend automated checks | PASS | `manage.py check` and `manage.py test` pass (9 tests); tests use the isolated test database. |
| Migration consistency | PASS | `python manage.py makemigrations --check --dry-run` reports no changes. No schema change was made for this work. |
| Frontend production build | PASS | `npm run build` passes after the audit changes. |
| Frontend automated interaction tests | NEEDS MANUAL ACTION | No frontend test script/framework is configured. Mock API interaction checks are manual and must remain distinct from real API checks. |
| Postman collection and setup documentation | PASS | Root and frontend READMEs and a credential-free Postman collection/environment are included. |
| GitHub repository / deployment URLs | NEEDS MANUAL ACTION | The workspace is not a Git repository; no remote or deployment URL is verified. |
| Final browser review and screen recording | NEEDS MANUAL ACTION | Perform a local browser walkthrough and record using the script in [SCREEN_RECORDING_SCRIPT.md](./SCREEN_RECORDING_SCRIPT.md). |

## Database safety

Read-only inspection found 0 comments and 2 contact messages before seeding. After the owner approved the exact preview, the local database received only the 6 labeled demo comments listed above. Existing portfolio content and contact messages were preserved. Backend tests use Django's disposable test database. The seed command defaults to dry-run, is idempotent, and leaves existing rows unchanged.

## Suggested final actions

1. Provide one genuine additional education or experience entry if it exists.
2. Complete local browser checks, capture the required recording, and verify repository/deployment links only if applicable.
