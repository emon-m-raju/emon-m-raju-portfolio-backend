# DevFolio screen-recording script (4–6 minutes)

Target length: about 5 minutes. Use the local development environment and demo/sanitized content only. Do not show credentials, tokens, private contact details, or environment files.

## 0:00–0:35 — Introduction

“This is DevFolio, a portfolio and blog built with Django REST Framework and a React/Vite frontend. Public visitors can explore the portfolio, read published posts, leave comments for moderation, and contact the owner. The owner dashboard is protected by JWT authentication.”

## 0:35–1:20 — Public portfolio

Show the home/profile and about sections, then skills, education, experience, and projects. Point out that the sections load portfolio data from the backend API rather than embedding personal content in the page. Switch the light/dark theme and briefly resize the viewport to demonstrate responsive behavior.

## 1:20–2:00 — Blog

Open the published blog listing and a post. Explain categories/tags, pagination if visible, and that public endpoints expose published posts while drafts remain owner-only. Mention that publishing validation requires at least 300 words.

## 2:00–2:35 — Visitor interactions

Show the contact form without submitting a message. Explain that public comments await owner approval and that the contact API is rate-limited. The existing comments are explicitly labeled fictional demo entries; do not present them as genuine visitor feedback.

## 2:35–4:20 — Owner dashboard

Sign in using a local test owner account without showing the password. Tour the overview, profile, skills/projects, blog, categories, and tags management pages. Then show Comments: filters, approval/unapproval, reply presentation, pagination, and empty/error/retry states. Show Messages: read/unread filters, message details, pagination, and read-state controls. Use mock data or an isolated local database for any write interaction.

## 4:20–4:45 — API and safety

Briefly show the Postman collection structure without revealing a populated token or credential. Explain that owner routes use JWT and owner-only permissions and that no real visitor messages/comments were used for interaction tests.

## 4:45–5:10 — Wrap-up

“The backend checks and production frontend build pass. The assignment data audit identifies one remaining content requirement: a second genuine education/experience entry. The comment threshold is met with clearly labeled fictional demo entries approved for this local project. No experience or achievement has been invented.”

## Recording checklist

- Close terminal panels or mask any output containing secrets.
- Use a local test account and a clean browser profile.
- Do not submit a real contact message or public comment during recording.
- Do not imply the seeded demo comments are real visitor feedback.
