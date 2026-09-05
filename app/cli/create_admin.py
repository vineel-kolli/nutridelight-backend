from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.admin_user import AdminUser
from app.services.auth_service import hash_password


MIN_PASSWORD_LENGTH = 12


def create_admin() -> None:
    username = input("Admin username: ").strip()

    if not username:
        print("Error: username cannot be empty.")
        return

    password = getpass("Admin password: ")
    password_confirmation = getpass("Confirm password: ")

    if password != password_confirmation:
        print("Error: passwords do not match.")
        return

    if len(password) < MIN_PASSWORD_LENGTH:
        print(
            f"Error: password must be at least "
            f"{MIN_PASSWORD_LENGTH} characters."
        )
        return

    db: Session = SessionLocal()

    try:
        existing_admin = db.execute(
            select(AdminUser).where(
                AdminUser.username == username,
            )
        ).scalar_one_or_none()

        if existing_admin is not None:
            print("Error: admin username already exists.")
            return

        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print(f"Admin '{username}' created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()