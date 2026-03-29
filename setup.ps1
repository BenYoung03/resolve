param(
	[string]$DbName = "database",
	[string]$AdminUsername = "testadmin",
	[string]$AdminEmail = "testadmin@resolve.com",
	[string]$AdminPassword = "Admin123!"
)

$ErrorActionPreference = "Stop"

$rootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$dbFilePath = Join-Path $rootPath ("{0}.db" -f $DbName)
$dbFileUriPath = $dbFilePath -replace "\\", "/"

if (Test-Path $dbFilePath) {
	Remove-Item $dbFilePath -Force
}

$env:DATABASE_URL = "sqlite:///$dbFileUriPath"
$env:TEST_ADMIN_USERNAME = $AdminUsername
$env:TEST_ADMIN_EMAIL = $AdminEmail
$env:TEST_ADMIN_PASSWORD = $AdminPassword

$seedScript = @'
import os

from app import app, db
from app.models import Category, Priority, Role, Status, User, ActivityLog

roles = ["Employee", "Agent", "Admin"]
priorities = ["Low", "Medium", "High", "Urgent", "Critical"]
categories = [
	"Hardware Issue",
	"Software Issue",
	"Network Issue",
	"Email Issue",
	"Printer Issue",
	"Account Access/Forgot Password",
	"Software Installation",
	"Other Inquiry",
]

statuses = ["Open", "Assigned", "In Progress", "On Hold", "Resolved", "Closed"]

with app.app_context():
	db.drop_all()
	db.create_all()

	role_rows = [Role(name=name, active=True) for name in roles]
	priority_rows = [Priority(name=name) for name in priorities]
	category_rows = [Category(name=name) for name in categories]
	status_rows = [Status(name=name) for name in statuses]

	db.session.add_all(role_rows + priority_rows + category_rows + status_rows)
	db.session.flush()

	role_by_name = {role.name: role for role in role_rows}
	admin = User(
		username=os.getenv("TEST_ADMIN_USERNAME", "testadmin"),
		email=os.getenv("TEST_ADMIN_EMAIL", "testadmin@example.com"),
		roleId=role_by_name["Admin"].RoleID,
	)
	admin.set_password(os.getenv("TEST_ADMIN_PASSWORD", "Admin123!"))

	db.session.add(admin)
	db.session.commit()

print("Database initialized successfully.")
'@

$pythonCandidates = @(
	(Join-Path $rootPath ".venv\Scripts\python.exe"),
	(Join-Path $rootPath "venv\Scripts\python.exe"),
	"python"
)

$pythonExe = $null
foreach ($candidate in $pythonCandidates) {
	if ($candidate -eq "python") {
		if (Get-Command python -ErrorAction SilentlyContinue) {
			$pythonExe = "python"
			break
		}
	}
	elseif (Test-Path $candidate) {
		$pythonExe = $candidate
		break
	}
}

if (-not $pythonExe) {
	throw "Python executable not found. Install Python or create a venv in this project."
}

& $pythonExe -c $seedScript

Write-Host "Created database file: $dbFilePath"
Write-Host "Test admin username: $AdminUsername"
Write-Host "Test admin email: $AdminEmail"
Write-Host "Test admin password: $AdminPassword"
