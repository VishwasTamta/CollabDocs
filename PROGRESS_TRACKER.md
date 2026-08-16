# CollabDocs — Progress Tracker

Tracks what's done vs. what's left against the assignment brief.

**How to use this file**

- Every open item is a `- [ ]` checkbox. Tick it (`- [x]`) in the same PR that finishes the work.
- Add your name in the **Owner** column when you pick something up, so two people don't duplicate effort.
- If you start something but don't finish, leave it unchecked and put `(WIP – <name>)` next to it rather than checking it early.
- If you add a brand-new feature that isn't in this file yet, add a row to the table in [Adding new items](#adding-new-items) instead of a random new heading, so the tracker stays one flat list anyone can scan.

---

## 1. Status at a glance

| Area | Status |
|---|---|
| 8 data models (UUID PK, TextChoices, constraints, self-FK, M2M) | ✅ Done |
| Migrations (clean from empty DB) | ✅ Done |
| Users API | ✅ Done |
| Workspaces API (create+atomic owner-admin, add member, list members) | ✅ Done |
| Documents API (CRUD, versioning, stats, tag-attach, filters) | ✅ Done |
| Tags API (CRUD, document listing, dedupe 409) | ✅ Done |
| Comments API (threaded CRUD, thread, summary) | ✅ Done |
| `post_save` signal → AuditLog on Document | ✅ Done |
| Transactions (workspace create, document+version, tag attach, comment create) | ✅ Done |
| Postman collection (Users/Workspaces/Documents/Tags/Comments folders) | ✅ Done |
| `.env.example`, pinned `requirements.txt` | ✅ Done |
| **Request-logging middleware** | ❌ Pending |
| **AuditLog read API** (`GET /api/audit-logs/`) | ❌ Pending |
| Workspace summary/stats endpoint (claimed in README, not built) | ❌ Pending |
| README accuracy (ownership table, feature list) | ⚠️ Needs cleanup |
| Automated tests (`tests.py` in every app is still the empty stub) | ⚠️ Not required by brief, optional |
| Demo video (Loom/Drive link in README) | ❌ Pending |

---

## 2. Pending items — required by the brief

### 2.1 Request-logging middleware
**Brief section 3.1 / 4.5.** Not implemented — `config/settings.py` `MIDDLEWARE` still only has Django's defaults; no custom middleware file exists anywhere in `apps/` or `config/`.

- [ ] Owner: __________
- [ ] Create `config/middleware.py` with a class implementing `__init__(self, get_response)` and `__call__(self, request)`
- [ ] Log, per request: HTTP method, endpoint path, response status code, time taken in ms
- [ ] Record time before/after `get_response(request)` and print the delta
- [ ] Register it in `config/settings.py` → `MIDDLEWARE`
- [ ] Confirm log lines print in the console while exercising the Postman collection (needed for the demo video)

### 2.2 AuditLog read API
**Brief section "Tags & Audit Logs" endpoints + rubric.** Currently broken/missing:

- `apps/auditlogs/serializers.py` imports `User` from `.models`, which doesn't exist in that app (should come from `apps.users.models`, or the serializer should just serialize `AuditLog` directly) — this will raise `ImportError` the moment it's touched.
- `apps/auditlogs/views.py` is still the unmodified `startapp` stub.
- No `apps/auditlogs/urls.py`, and `config/urls.py` never includes an auditlogs route.
- The Postman collection already has a placeholder request named **"Filter Audit Logs (pending implementation)"** in the Audit Logs folder — confirming this was left for later.

- [ ] Owner: __________
- [ ] Fix `apps/auditlogs/serializers.py` — write an `AuditLogSerializer` (read-only) with `select_related("actor")`
- [ ] Implement `AuditLogViewSet` (or a read-only `ListAPIView`) in `apps/auditlogs/views.py`
- [ ] Support filters per the brief (e.g. `?model_name=`, `?action=`, `?actor=`, date range) — reuse the `gte/lte/icontains` pattern already used in Documents/Comments
- [ ] Add `apps/auditlogs/urls.py` and register it in `config/urls.py` under `api/`
- [ ] Update the Postman "Filter Audit Logs" request to a working example and rename it (drop "pending implementation")
- [ ] Verify AuditLog rows written by the Document signal, tag-attach, and comment-create actions are all visible through this endpoint

### 2.3 Endpoint count check
**Brief: "All 17 endpoints tested and working in Postman before submission."**

- [ ] Owner: __________
- [ ] Once 2.1 and 2.2 land, recount actual endpoints (routers + `@action`s) against the 17 the brief expects and reconcile any gap
- [ ] Re-export the Postman collection after the audit-logs endpoint is real

---

## 3. Pending items — README / project hygiene

These aren't graded code, but they're part of the "incomplete submission marked down" risk since README accuracy affects the GitHub-repo deliverable.

- [ ] Owner: __________ — Remove or implement the **"Workspace Summary"** bullet in `README.md` under API Modules → Workspaces; no such endpoint exists in `apps/workspaces/views.py` today (only `create` and `members`)
- [ ] Owner: __________ — Fill in the **Module Ownership** table in `README.md` (currently all blank) and the matching table in `CONTRIBUTING.md`
- [ ] Owner: __________ — Fill in the **Contributors** list in `README.md` (3 of 4 slots blank)
- [ ] Owner: __________ — Tick off the **Pending Tasks** checklist at the bottom of `README.md` as items in this tracker close (or just delete that section and point it at this file)

---

## 4. Required submission deliverables (brief section 6)

| Deliverable | Status | Notes |
|---|---|---|
| 6.1 GitHub repo (public, `.env.example`, pinned `requirements.txt`, clean migrations, README, Postman `.json` at root) | ⚠️ Mostly done | README needs the cleanup in §3 |
| 6.2 Postman collection (all endpoints, sample POST/PUT bodies, folders per module) | ⚠️ Mostly done | Blocked on Audit Logs endpoint (§2.2) |
| 6.3 Demo video (5–10 min, atomic-transaction rollback, middleware logs, an aggregation endpoint, signal-written AuditLog) | ❌ Not started | Can't fully record until middleware (§2.1) exists — the brief explicitly requires showing middleware logs in the console |

- [ ] Owner: __________ — Record demo video once §2.1 and §2.2 are done
- [ ] Owner: __________ — Upload to Loom/Drive and add the link to `README.md`

---

## 5. Optional / not required by the brief

Not graded, but worth a line so nobody "fixes" it by surprise mid-submission crunch.

- [ ] `tests.py` in every app is still the default one-line Django stub — the brief only asks for Postman-verified endpoints, not automated tests, so leave as-is unless the team wants extra coverage.

---

## Adding new items

If new work comes up that isn't covered above, add a row here instead of scattering notes elsewhere:

| Item | Owner | Status | Notes |
|---|---|---|---|
| | | | |
