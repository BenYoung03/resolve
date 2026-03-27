from app import app, db
from app.models import Role

# List of roles to populate
roles = ["Admin", "Agent", "Employee"]

with app.app_context():
    for r in roles:
        # Check if role already exists
        if not Role.query.filter_by(name=r).first():
            new_role = Role(name=r)
            db.session.add(new_role)
    db.session.commit()
    print("Roles populated successfully!")