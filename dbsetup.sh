#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${1:-database}"
ADMIN_USERNAME="${2:-testadmin}"
ADMIN_EMAIL="${3:-testadmin@resolve.com}"
ADMIN_PASSWORD="${4:-Admin123!}"
ADMIN_NOTIFICATIONS="${5:-0}"

ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_FILE_PATH="$ROOT_PATH/${DB_NAME}.db"
DB_FILE_URI_PATH="$DB_FILE_PATH"

if [ -f "$DB_FILE_PATH" ]; then
    rm -f "$DB_FILE_PATH"
fi

export DATABASE_URL="sqlite:///$DB_FILE_URI_PATH"
export TEST_ADMIN_USERNAME="$ADMIN_USERNAME"
export TEST_ADMIN_EMAIL="$ADMIN_EMAIL"
export TEST_ADMIN_PASSWORD="$ADMIN_PASSWORD"

read -r -d '' SEED_SCRIPT <<'PYTHON' || true
import os

from app import app, db
from app.models import Category, Priority, Role, Status, User

ROLE_DEFINITIONS = [
    {"name": "Employee", "active": True, "permissions": ""},
    {"name": "Agent", "active": True, "permissions": ""},
    {"name": "Admin", "active": True, "permissions": ""},
]

PRIORITIES = ["Low", "Medium", "High", "Urgent", "Critical"]

CATEGORIES = [
    "Hardware Issue",
    "Software Issue",
    "Network Issue",
    "Email Issue",
    "Printer Issue",
    "Account Access/Forgot Password",
    "Software Installation",
    "Other Inquiry",
]

STATUSES = ["Open", "Assigned", "In Progress", "On Hold", "Resolved", "Closed"]

with app.app_context():
    db.drop_all()
    db.create_all()

    role_rows = [
        Role(
            name=role["name"],
            active=role["active"],
            permissions=role["permissions"]
        )
        for role in ROLE_DEFINITIONS
    ]
    priority_rows = [Priority(name=name) for name in PRIORITIES]
    category_rows = [Category(name=name) for name in CATEGORIES]
    status_rows = [Status(name=name) for name in STATUSES]

    db.session.add_all(role_rows + priority_rows + category_rows + status_rows)
    db.session.flush()

    role_by_name = {role.name: role for role in role_rows}

    admin = User(
        username=os.getenv("TEST_ADMIN_USERNAME", "testadmin"),
        email=os.getenv("TEST_ADMIN_EMAIL", "testadmin@example.com"),
        roleId=role_by_name["Admin"].RoleID,
        notifications=bool(int(os.getenv("TEST_ADMIN_NOTIFICATIONS", "0")))
    )
    admin.set_password(os.getenv("TEST_ADMIN_PASSWORD", "Admin123!"))

    db.session.add(admin)
    db.session.commit()

print("Database initialized successfully.")
PYTHON

PYTHON_EXE=""

if [ -x "$ROOT_PATH/.venv/bin/python" ]; then
    PYTHON_EXE="$ROOT_PATH/.venv/bin/python"
elif [ -x "$ROOT_PATH/venv/bin/python" ]; then
    PYTHON_EXE="$ROOT_PATH/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_EXE="python"
else
    echo "Python executable not found. Install Python or create a venv in this project." >&2
    exit 1
fi

printf '%s' "$SEED_SCRIPT" | "$PYTHON_EXE"

echo "Created database file: $DB_FILE_PATH"
echo "Test admin username: $ADMIN_USERNAME"
echo "Test admin email: $ADMIN_EMAIL"
echo "Test admin password: $ADMIN_PASSWORD"
