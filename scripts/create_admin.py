"""
CLI script to create an admin user.

Usage:
    python -m scripts.create_admin
    python -m scripts.create_admin --username myadmin --password mysecret
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env')


async def main():
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--username", default="admin", help="Admin username (default: admin)")
    parser.add_argument("--password", default="admin123", help="Admin password (default: admin123)")
    parser.add_argument("--display-name", default="Administrator", help="Display name")
    args = parser.parse_args()

    from app.database import engine
    from app.models import Base as ModelsBase
    from app.models.user import User  # noqa: ensure model is registered
    from app.services.user_service import user_service

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)

    # Check if user already exists
    existing = await user_service.get_by_username(args.username)
    if existing:
        print(f"User '{args.username}' already exists (id={existing.id}, role={existing.role}).")
        return

    user = await user_service.create_user(
        username=args.username,
        password=args.password,
        display_name=args.display_name,
        role="admin",
    )
    print(f"Admin user created successfully:")
    print(f"  ID:       {user.id}")
    print(f"  Username: {user.username}")
    print(f"  Role:     {user.role}")
    print(f"  Display:  {user.display_name}")


if __name__ == "__main__":
    asyncio.run(main())
