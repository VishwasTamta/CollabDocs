# CollabDocs Backend API

CollabDocs is a Django REST Framework based backend application that allows users to create workspaces, collaborate on documents, maintain version history, add comments, manage tags, and track document activities through audit logs.

This project is developed as part of the Airtribe Backend Assignment.

---

# Tech Stack

- Python 3.12+
- Django
- Django REST Framework
- PostgreSQL
- python-decouple
- UUID Primary Keys

---

# Features

- User Management
- Workspace Management
- Workspace Members with Roles
- Document Versioning
- Threaded Comments
- Tags
- Audit Logs
- Request Logging Middleware
- Transactions using `transaction.atomic()`
- Django Signals
- Filtering & Searching
- Aggregations using Count and annotate

---

# Project Structure

```
CollabDocs/
│
├── apps/
│   ├── users/
│   ├── workspaces/
│   ├── documents/
│   ├── comments/
│   ├── tags/
│   ├── auditlogs/
│   └── common/
│
├── config/
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# Installation

Clone Repository

```bash
git clone <repository-url>
```

Create Virtual Environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env`

```
SECRET_KEY=your_secret_key

DEBUG=True

DB_NAME=collabdocs

DB_USER=postgres

DB_PASSWORD=your_password

DB_HOST=localhost

DB_PORT=5432
```

---

# Database Setup

Create PostgreSQL database

```sql
CREATE DATABASE collabdocs;
```

Run migrations

```bash
python manage.py makemigrations

python manage.py migrate
```

Start Server

```bash
python manage.py runserver
```

---

# Git Workflow

## Main Branch

```
main
```

Never push directly to main.

---

## Create your own branch

Example

```bash
git checkout -b rahul
```

or

```bash
git checkout -b your-name
```

---

## Before starting work

```bash
git checkout main

git pull origin main
```

---

## After completing work

```bash
git add .

git commit -m "Meaningful commit message"

git push origin your-branch
```

Create Pull Request to `main`.

---

# Module Ownership

| Module | Owner | Status |
|---------|-------|--------|
| Users | | |
| Workspace | | |
| Documents | | |
| Comments | | |
| Tags | | |
| Audit Logs | | |
| Middleware | | |
| Signals | | |

---

# API Modules

## Users

- Create User
- Get User

---

## Workspaces

- Create Workspace
- Get Workspace
- Add Member
- List Members
- Workspace Summary

---

## Documents

- Create Document
- Update Document
- List Documents
- Document Versions
- Document Stats
- Add Tags

---

## Comments

- Create Comment
- List Comments

---

## Tags

- Create Tag

---

## Audit Logs

- Filter Audit Logs

---

# Assignment Concepts

- UUID Primary Keys
- ModelViewSet
- Serializer Validation
- SerializerMethodField
- TextChoices
- transaction.atomic()
- Signals
- Middleware
- annotate()
- aggregate()
- Count()
- select_related()
- ManyToManyField
- Self-referential ForeignKey
- UniqueConstraint

---

# Team Guidelines

- Follow PEP-8 coding style.
- Do not modify another member's module without discussion.
- Keep commits small and meaningful.
- Test your endpoints in Postman before pushing.
- Resolve merge conflicts before creating a Pull Request.
- Keep serializers, views, and models organized.
- Avoid commented or unused code.

---

# Pending Tasks

- [ ] Models
- [ ] Serializers
- [ ] ViewSets
- [ ] URLs
- [ ] Middleware
- [ ] Signals
- [ ] Transactions
- [ ] Testing
- [ ] Postman Collection
- [ ] Documentation

---

# Contributors

- Rahul Chauhan
- ____________________
- ____________________
- ____________________
