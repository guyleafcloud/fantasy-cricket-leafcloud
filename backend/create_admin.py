#!/usr/bin/env python3
"""
Create Admin User
=================
Script to create the first admin user for the fantasy cricket platform.
Run this once after deployment to set up admin access.

Usage:
    python3 create_admin.py --email admin@example.com --name "Admin User"
"""

import sys
import argparse
import os
from getpass import getpass
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Import User model from centralized database schema
from database_models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(email: str, full_name: str, password: str, database_url: str):
    """Create an admin user in the database"""

    # Create engine and session
    engine = create_engine(database_url)
    # Don't create tables - they should already exist from main.py
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            if existing_user.is_admin:
                print(f"   This user is already an admin.")
            else:
                # Upgrade existing user to admin
                response = input(f"   Would you like to make this user an admin? (y/n): ")
                if response.lower() == 'y':
                    existing_user.is_admin = True
                    db.commit()
                    print(f"✅ User {email} has been upgraded to admin!")
                else:
                    print("   No changes made.")
            return

        # Hash the password
        password_hash = pwd_context.hash(password)

        # Create new admin user
        admin_user = User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            is_admin=True,
            is_active=True,
            is_verified=True  # Auto-verify admin
        )

        db.add(admin_user)
        db.commit()
        # Note: refresh removed to avoid UUID/VARCHAR casting issues

        print(f"\n✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {full_name}")
        print(f"   Admin: Yes")
        print(f"\n🔐 You can now login with these credentials at /api/auth/login")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description='Create admin user for Fantasy Cricket')
    parser.add_argument('--email', required=True, help='Admin email address')
    parser.add_argument('--name', required=True, help='Admin full name')
    parser.add_argument('--password', help='Admin password (will prompt if not provided)')
    parser.add_argument('--database-url', help='Database URL (defaults to DATABASE_URL env var)')

    args = parser.parse_args()

    # Get password
    if args.password:
        password = args.password
    else:
        password = getpass("Enter admin password: ")
        password_confirm = getpass("Confirm password: ")

        if password != password_confirm:
            print("❌ Passwords do not match!")
            sys.exit(1)

    if len(password) < 8:
        print("❌ Password must be at least 8 characters long!")
        sys.exit(1)

    # Get database URL
    database_url = args.database_url or os.getenv(
        "DATABASE_URL",
        "postgresql://cricket_admin:password@fantasy_cricket_db:5432/fantasy_cricket"
    )

    print(f"\n🏏 Creating admin user...")
    print(f"   Email: {args.email}")
    print(f"   Name: {args.name}")
    print(f"   Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    print()

    create_admin_user(args.email, args.name, password, database_url)

if __name__ == "__main__":
    main()
