# Contributing Guidelines

Thank you for contributing to the CollabDocs Backend project.

Please follow these guidelines to keep the repository clean and avoid merge conflicts.

---

# Tech Stack

- Python 3.12+
- Django
- Django REST Framework
- PostgreSQL

---

# Branch Strategy

Never work directly on the `main` branch.

Create your own branch.

Example:

```bash
git checkout -b rahul
```

```bash
git checkout -b aman
```

```bash
git checkout -b priya
```

---

# Before Starting Work

Always pull the latest code.

```bash
git checkout main

git pull origin main

git checkout your-branch

git merge main
```

---

# Commit Messages

Use meaningful commit messages.

Good examples

```text
Add User model

Implement Workspace APIs

Add Document Version serializer

Fix WorkspaceMember validation

Implement AuditLog signal
```

Avoid

```text
changes

update

done

fixed

code
```

---

# Pull Request Checklist

Before creating a Pull Request ensure

- Code runs successfully
- No merge conflicts
- No commented code
- PEP-8 followed
- Endpoints tested in Postman
- Migrations included if models changed

---

# Coding Standards

## Models

- UUIDField as Primary Key
- TextChoices for enums
- related_name on relationships
- Meaningful __str__ methods

---

## Serializers

- Use ModelSerializer
- Add validation where required
- Use SerializerMethodField only when needed

---

## Views

- Use ModelViewSet
- Use @action for custom endpoints
- Use transaction.atomic() where required
- Return proper HTTP status codes

---

## Query Optimization

Use

- select_related()
- prefetch_related()
- annotate()
- aggregate()

Avoid unnecessary database queries.

---

# Testing

Every endpoint must be tested using Postman before pushing.

---

# Folder Ownership

| Module | Owner |
|----------|--------|
| Users | |
| Workspaces | |
| Documents | |
| Comments | |
| Tags | |
| Audit Logs | |
| Middleware | |
| Signals | |

Update this table once modules are assigned.

---

# Do Not

- Push directly to main
- Commit `.env`
- Commit `venv`
- Modify another person's module without discussion
- Leave print() statements in production code

---

# Contact

If your changes affect another module, inform the respective owner before merging.