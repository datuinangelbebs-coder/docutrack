
from database import SessionLocal, User

ADMIN_EMAIL = "a.datuin.150960.tc@umindanao.edu.ph"

with SessionLocal() as db:
    user = db.query(User).filter_by(email=ADMIN_EMAIL).first()

    if user is None:
        print("Account not found.")
    else:
        user.role = "admin"
        user.is_active = True
        db.commit()

        print("Account role successfully updated!")
        print("Name:", user.first_name, user.last_name)
        print("Role:", user.role)
        print("Active:", user.is_active)
