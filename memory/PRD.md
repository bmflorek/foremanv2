# ShopTrack — Manufacturing Project Tracking (PRD)

## Original Problem Statement
Pivot the existing task-management tool into a **manufacturing project tracking system** for a custom window & door fabrication shop:
- Add **Jobs** with all pertinent info (tracking, costs/budget, spec sheet).
- List all **Units** on a job (W1/D1/BF1/SL1, handing suffix W1a/W1b).
- **In/Out tracker** for units leaving the facility (welding, painting, etc.) to a **vendor list**.
- **Kanban board** for large screens showing shop units (Not Started → In Fab → Out for Process → Complete).
- Refactor the monolithic codebase into a clean structure. Drop VibeMeeting/transcription entirely.

## User Decisions (June 2026)
- Database: **keep MongoDB** (Supabase rejected).
- Auth: **login only, no teams**. Existing session-token auth retained.
- Job number: 2-digit year + 3-digit sequence (`^\d{5}$`, e.g. 26207).
- Job specs: paint type, color, hardware brand, hardware name, hinge type, hinge color, custom hardware, threshold color, glazing bead type, SDL type, glass type + free-form additional notes.
- Units: W=window, D=door, BF=bifold, SL=slider (type auto-derived from prefix, overridable); fields: unit #, type, description, W×H, qty, location, status, notes.
- Vendors: name, service, contact, phone, email, address, notes → populate check-out dropdown.
- Budget: job has **sold amount**; **Purchase Orders** (auto `{job}-PO-NN`, vendor, line items qty×unit cost, status) deduct from sold amount → remaining budget + over-budget warning. Cancelled POs excluded.
- Kanban columns: Not Started → In Fab → Out for Process → Complete.

## Architecture
- **Backend** (FastAPI + Motor/MongoDB): `/app/backend`
  - `server.py` — app + router mounting under `/api`
  - `core/db.py`, `core/auth.py` (Bearer session tokens), `core/email.py`
  - `models/` — user, job (JobSpecs), unit, vendor, movement, purchase_order
  - `routers/` — auth, jobs, units, vendors, movements, purchase_orders, board
  - `seed.py` — idempotent demo data (user, 4 vendors, job 26207 w/ 8 units)
- **Frontend** (React + Tailwind + shadcn): `/app/frontend/src`
  - `lib/api.js` (axios w/ token), `lib/constants.js`
  - pages: LoginPage, Dashboard (shell), JobsPage, JobDetailPage, ShopBoardPage (`tv` prop for `/board`), TrackerPage, VendorsPage
  - components: JobFormDialog, UnitFormDialog, POFormDialog, VendorFormDialog, StatusBadge, BudgetBar, FormControls, PageHeader, job/{SpecsSheet,UnitsTab,PurchaseOrdersTab,MovementLog}
- Design: dark industrial theme (`/app/design_guidelines.json`) — slate bg, amber accent, Barlow Condensed / JetBrains Mono / Plus Jakarta Sans.

## Key API Endpoints
- Auth: `POST /api/auth/register|login|logout`, `GET /api/auth/me`, password reset OTP endpoints
- Jobs: `GET/POST /api/jobs`, `GET/PUT/DELETE /api/jobs/{id}` (enriched with `budget`, `unit_counts`)
- Units: `GET/POST /api/jobs/{id}/units`, `GET/PATCH/DELETE /api/units/{id}` (status locked while checked out)
- Vendors: `GET/POST /api/vendors`, `PUT/DELETE /api/vendors/{id}`
- Movements: `POST /api/movements` (direction out|in), `GET /api/movements?job_id&unit_id&limit`, `GET /api/movements/out`
- POs: `GET/POST /api/jobs/{id}/purchase-orders`, `PUT/DELETE /api/purchase-orders/{id}`
- Board: `GET /api/board` (active/on_hold jobs only)

## Implemented (June 2026)
- [x] Backend refactor into core/models/routers; VibeMeeting, teams, approvals, comments, notifications removed
- [x] Jobs CRUD + spec sheet + budget calc
- [x] Units CRUD w/ number normalization, type derivation, natural sort
- [x] Vendors CRUD
- [x] In/Out tracker (check-out/in, currently-out list w/ days out, movement log)
- [x] Purchase orders w/ auto numbering, live totals, over-budget alerts
- [x] Shop Board kanban w/ drag-drop + standalone TV mode (`/board`, 15s auto-refresh, fullscreen)
- [x] New dark industrial UI; login/register/reset page
- [x] Testing: iteration_1 — 26/26 backend tests + all frontend flows passed
- [x] Job Issues Log tab (log/resolve/reopen, severity, unit link, open-count badges)
- [x] Customer Approvals tab (drawings / color sample / hardware sign-offs w/ approver, date, notes, revoke)
- [x] Shop Board job filter (`?job=`) + grouping under job headers (board + TV mode)
- [x] Vendor turnaround stats (avg days out, trips, out now; sort slowest first)
- [x] Testing: iteration_2 — 32/32 backend tests + all frontend flows passed
- [x] Due-date urgency on Shop Board cards (amber ring ≤7d, red pulsing ring when overdue, chip label, legend; complete units excluded) — self-tested via screenshot

## Morning Digest (June 2026)
- Daily email at 6:30 AM America/New_York via platform cron (`.emergent/crons.yml` → `POST /api/cron/digest`, Bearer WEBHOOK_CRON_SECRET, idempotent by X-Webhook-Id, work backgrounded).
- Email sent through Emergent managed email integration (EMERGENT_EMAIL_KEY, EMAIL_FROM_NAME=ShopTrack) — user's Resend key NOT used (playbook). Password-reset OTP email also moved to this channel.
- Contents: overdue active/on_hold jobs with open units, units out at vendors ≥7 days, count of open high-severity issues, link to Shop Board.
- Recipients managed in-app: Jobs page → "Morning Digest" dialog (add/remove emails, enable toggle, "If sent right now" preview, send test, recent runs). Seeded recipient: bmflorek@gmail.com.
- Endpoints: `GET/PUT /api/settings/digest`, `GET /api/digest/preview`, `POST /api/digest/send-test`, `POST /api/cron/digest`.
- Verified: test digest delivered, cron endpoint 401 without secret, duplicate run_id → skipped.

## Code Review Pass (June 2026)
- seed.py reads SEED_DEMO_EMAIL/SEED_DEMO_PASSWORD from backend/.env (no hardcoded creds)
- Refactors: useAuthForm hook + LoginPage subcomponents; POFormDialog → LineItemsEditor w/ stable keys; DigestSettingsDialog → RecipientsEditor/DigestPreview/RecentRuns; JobDetailPage → JobHeader/JobSummary; UnitsTab → UnitRow; render_digest + cron_digest split into helpers; board.py type hints
- Hook deps: load() wrapped in useCallback (JobsPage, VendorsPage, DigestSettingsDialog); Dashboard logout logs errors
- Declined: localStorage→httpOnly cookie session (would require auth re-architecture; tracked in backlog); `is None` findings were false positives; `_assert_safe_email` kept verbatim per email playbook
- Verified: iteration_3 — 40/40 backend + all frontend regression flows passed

## Additional Endpoints (iteration 2)
- Issues: `GET/POST /api/jobs/{id}/issues?status=`, `PATCH/DELETE /api/issues/{id}`
- Approvals: `PUT /api/jobs/{id}/approvals/{drawings|color_sample|hardware}`
- Board: `GET /api/board?job_id=` (+ `jobs` list in response)
- Vendors: `GET /api/vendors` now includes `stats {completed_trips, avg_days_out, currently_out}`

## Backlog
- P2: Unit-level attachments (drawings/photos) via object storage
- P2: Export job spec sheet / PO to PDF
- P2: Upgrade password hashing (sha256 → bcrypt) and move session token to httpOnly cookie via integration playbook
