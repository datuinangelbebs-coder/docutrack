
from getpass import getpass

from werkzeug.security import generate_password_hash

from database import SessionLocal, User


def create_admin():

    print("\n===== UMTC ADMIN ACCOUNT CREATION =====\n")

    first_name = input("Admin First Name: ").strip()
    last_name = input("Admin Last Name: ").strip()
    email = input("UM Institutional Email: ").strip().lower()

    password = getpass("Create Admin Password: ")
    confirm_password = getpass("Confirm Admin Password: ")

    if not all([first_name, last_name, email, password]):
        print("\nError: All fields are required.")
        return

    if password != confirm_password:
        print("\nError: Passwords do not match.")
        return

    if len(password) < 8:
        print("\nError: Password must have at least 8 characters.")
        return

    with SessionLocal() as db:

        existing_user = db.query(User).filter_by(
            email=email
        ).first()

    if existing_user:
        print("\nAccount already exists!")
        print("Name:", existing_user.first_name, existing_user.last_name)
        print("Email:", existing_user.email)
        print("Role:", existing_user.role)
        print("Active:", existing_user.is_active)
        return

        admin = User(
            first_name=first_name,
            last_name=last_name,
            middle_name=None,
            student_id=None,
            course=None,
            year_level=None,
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print("\nAdmin account created successfully!")
        print("Account Role: Admin")
        print("You can now log in using your admin credentials.")


if __name__ == "__main__":
    create_admin()
