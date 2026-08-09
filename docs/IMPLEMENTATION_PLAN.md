# Implementation plan — Documents & Versioning, Tags, Comments

Owner: Nelson
Branch: `nelson-docs-tags-comments`

This plan covers the three modules assigned to me. Users, Workspaces, the
request-logging middleware and the AuditLog read API belong to other team
members and are explicitly out of scope here — see [Out of scope](#out-of-scope).

Setup and run instructions live in the root [README.md](../README.md).

---

## 1. Where the repo stands

Everything below was verified by reading the code on `main` at `4e3cdc8`.

| Area | State |
|---|---|
| Models — all 8 | **Done.** UUID PKs, `TextChoices`, `UniqueConstraint` on `WorkspaceMember`, self-referential FK on `Comment`, M2M between `Tag` and `Document`. |
| Migrations | **Done and applying cleanly** from an empty database. |
| Users | Serializer + `ModelViewSet` + router. Works. |
| Workspaces | Serializer + viewset with atomic create and the `members` action. Works. |
| **Documents** | Models only. `serializers.py` empty, `views.py` is the `startapp` stub, no `urls.py`, not routed in `config/urls.py`. |
| **Tags** | Models only. `serializers.py` empty, `views.py` is a stub. |
| **Comments** | Models only. `serializers.py` empty, `views.py` is a stub. |
| AuditLogs | Model only. `serializers.py` mistakenly imports a non-existent `User` from `.models`. |
| Middleware | Not written. |
| Signals | Not written. No `signals.py`, no `AppConfig.ready()`. |

Two defects found while getting the project to boot, both fixed in the first
commit on this branch:

1. `djangorestframework==3.17.2` cannot run on `Django==6.1` (it imports
   `cc_delim_re`, removed in Django 6.1). Nothing ran at all — every
   `manage.py` command died at import time. Pinned to `3.18.0`.
2. No `.env.example`, which the submission checklist requires.

---

## 2. Conventions I am following

Taken from the existing `users` and `workspaces` code so my modules read like
the rest of the repo:

- One app per domain under `apps/`, each with its own `urls.py` exposing a
  `DefaultRouter`, included from `config/urls.py` under the `api/` prefix.
- `ModelViewSet` for CRUD; `@action` for anything non-standard.
- `queryset` declared on the class with `select_related()` / `annotate()`
  already applied (the pattern in `WorkspaceViewSet`).
- `SerializerMethodField` reads a value that `annotate()` already computed and
  falls back to a live count — the `get_members_count` pattern in
  `WorkspaceSerializer`.
- Explicit `try/except IntegrityError` returning `409`, as in
  `WorkspaceViewSet.members`.
- Model `Meta` always sets `verbose_name`, `verbose_name_plural`, `db_table`.
- Four-space indent, double quotes, trailing-comma multi-line signatures.

---

## 3. Delivery order

Each numbered item is one commit, tested against a running server before it is
pushed. Later items depend on earlier ones, so the order matters.

### Commit 1 — `docs/`
This plan. No code.

### Commit 2 — Documents and versioning
The core of the module. Everything else hangs off it.

**`apps/documents/serializers.py`**
- `DocumentVersionSerializer` — read-only; `saved_by_name` as a
  `SerializerMethodField`.
- `DocumentSerializer` — adds `version_count`, `latest_version` and
  `tag_names` as `SerializerMethodField`s; a write-only optional `saved_by`
  so the caller can say who performed a save.
- Custom validation:
  - `validate_title` — rejects titles under 3 characters after stripping.
  - `validate()` — rejects a `created_by` who is not a `WorkspaceMember` of
    the target `workspace`. Returns `400` with a readable message.

**`apps/documents/views.py`** — `DocumentViewSet(ModelViewSet)`
- `queryset = Document.objects.select_related("workspace", "created_by")`
- `create()` and `update()` each wrap the save **and** the `DocumentVersion`
  insert in one `transaction.atomic()`. `version_number` is computed as
  `document.versions.count() + 1` inside that block, per the brief.
- `get_queryset()` list filtering:
  - `workspace`, `created_by`, `status` (exact)
  - `status_in` → `status__in`
  - `updated_after` / `updated_before` → `updated_at__gte` / `__lte`
  - `search` → `Q(title__icontains=...) | Q(content__icontains=...)`
    — this is the required **Q-object OR filter**
- `@action(detail=True) versions` — version history, `select_related("saved_by")`.
- `@action(detail=False) stats` — `aggregate()` for totals plus
  `annotate(Count(...))` grouped by status and by workspace.
- `values_list("id", flat=True)` where only ids are needed.

**`apps/documents/signals.py`** + `DocumentsConfig.ready()`
- `post_save` on `Document`. Writes an `AuditLog` with
  `actor=instance.created_by`, `action='created'|'updated'`,
  `model_name='Document'`, `object_id=str(instance.pk)`.
- Note on `instance._state.adding`: the brief suggests it to tell create from
  update, but by the time `post_save` fires Django has already flipped it to
  `False`. The handler therefore reads the `created` flag the signal passes and
  keeps `_state.adding` only as a defensive fallback.
- Because `save()` happens inside the view's `transaction.atomic()` block, the
  signal's `AuditLog` insert lands in that same transaction — satisfying "the
  AuditLog must be written inside the same atomic block" without a second,
  duplicate write in the view.

**`apps/documents/urls.py`** + registration in `config/urls.py`.

### Commit 3 — Tags
Depends on commit 2 for the document queryset helpers.

**`apps/tags/serializers.py`**
- `TagSerializer` with a `document_count` `SerializerMethodField`.
- `validate_name` — strips, lowercases, rejects names under 2 characters.
  Normalising here is what makes the `unique=True` on `Tag.name` meaningful.
- `AttachTagsSerializer` — validates the `{"tags": ["a", "b"]}` body for the
  attach action.

**`apps/tags/views.py`** — `TagViewSet(ModelViewSet)`
- `queryset` annotated with `Count("documents")`.
- `?search=` → `name__icontains`; `?names=` → `name__in`.
- `create()` catches `IntegrityError` → `409` for a duplicate tag name.
- `@action(detail=True) documents` — documents carrying this tag.

**Back in `apps/documents/views.py`**
- `@action(detail=True, methods=["post"]) tags` — attach tags to a document by
  name, creating any that don't exist. Whole thing in one
  `transaction.atomic()` with an explicit `AuditLog` write (`action='tagged'`)
  in the same block, because no model `post_save` fires for an M2M change.
- `?tag=` filter added to the document list.

### Commit 4 — Comments
Depends on commit 2 (documents must exist to comment on).

**`apps/comments/serializers.py`**
- `CommentSerializer` with `replies` (recursive) and `reply_count` as
  `SerializerMethodField`s, plus `author_name`.
- Custom validation in `validate()`:
  - a `parent` comment must belong to the **same document** — otherwise `400`;
  - the `author` must be a `WorkspaceMember` of the document's workspace.

**`apps/comments/views.py`** — `CommentViewSet(ModelViewSet)`
- `queryset` with `select_related("document", "author", "parent")` and
  `prefetch_related("replies")`.
- List returns top-level comments with nested replies by default;
  `?include_replies=true` flattens.
- Filters: `?document=`, `?author=`, `?search=` (`content__icontains`),
  `?created_after` / `?created_before` (`gte` / `lte`), `?parent=`.
- `create()` in `transaction.atomic()` with an `AuditLog` write in the block.
- `@action(detail=True) thread` — one comment plus its whole reply tree.
- `@action(detail=False) summary` — `annotate(Count("comments"))` per document.

### Commit 5 — Postman collection
`CollabDocs.postman_collection.json` at the repo root, folders for Documents,
Tags and Comments, with sample bodies for every POST/PUT and collection
variables chained from the create responses. The Users and Workspaces folders
are added by their owners; if they haven't landed by submission time I'll add
minimal versions so the collection runs end to end.

---

## 4. How the brief's requirements are covered by this scope

| Requirement | Where |
|---|---|
| `select_related` on nested data | every viewset queryset in commits 2–4 |
| `filter()` with `gte` / `lte` / `in` / `icontains` | document list, comment list, tag list |
| `Q` objects for OR | `DocumentViewSet.get_queryset()` `?search=` |
| `aggregate()` / `annotate()` with `Count` — 3 endpoints | `documents/stats/`, `tags/` list, `comments/summary/` |
| `values_list()` for ids only | tag attach, document stats |
| ≥2 `SerializerMethodField` | 8 across the three modules |
| ≥2 custom serializer validations | documents (2), tags (1), comments (2) |
| `transaction.atomic()` on document save + version | `DocumentViewSet.create/update` |
| AuditLog inside the same atomic block | via the `post_save` signal, and explicitly for tag attach / comment create |
| `post_save` signal on Document | `apps/documents/signals.py`, connected in `DocumentsConfig.ready()` |
| `IntegrityError` → `409` | tag create (duplicate name) |
| `DoesNotExist` handled | tag attach, comment parent lookup |
| `@action` for non-standard endpoints | `versions`, `stats`, `tags`, `thread`, `summary`, `documents` |

---

## 5. Testing loop per commit

Nothing gets pushed until it has been through this:

1. `python manage.py makemigrations --check --dry-run` — confirm no model drift.
2. `python manage.py check` — no system-check errors.
3. `python manage.py runserver` and exercise every new route, including the
   failure cases:
   - duplicate tag name → `409`
   - reply whose parent belongs to another document → `400`
   - non-member author → `400`
   - unknown id → `404`
4. Confirm the version row count grows by one per document save, and that an
   `AuditLog` row appears for each create/update.
5. Commit, then push the branch.

---

## Out of scope

Owned by other team members; I will not touch these files:

- `apps/users/` and `apps/workspaces/`
- The request-logging middleware (`config/middleware.py` + `MIDDLEWARE`)
- The AuditLog **read** API (`GET /api/audit-logs/` with filters) and the
  broken import in `apps/auditlogs/serializers.py`

My modules **write** AuditLog rows, so the AuditLog owner's list endpoint will
have data to return as soon as it lands. If either the middleware or the
AuditLog API is still missing near the submission deadline, I'll raise it with
the team rather than silently absorb it.
