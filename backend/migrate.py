#!/usr/bin/env python3
"""
Database migration management script
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def init_migrations():
    """Initialize Alembic (only needed once)"""
    print("🚀 Initializing database migrations...")
    return run_command(
        ["alembic", "init", "alembic"], 
        "Initializing Alembic configuration"
    )

def create_migration(message="Auto migration"):
    """Create a new migration"""
    return run_command(
        ["alembic", "revision", "--autogenerate", "-m", message],
        f"Creating migration: {message}"
    )

def upgrade_database():
    """Apply all pending migrations"""
    return run_command(
        ["alembic", "upgrade", "head"],
        "Applying database migrations"
    )

def downgrade_database(revision="base"):
    """Downgrade database to specific revision"""
    return run_command(
        ["alembic", "downgrade", revision],
        f"Downgrading database to: {revision}"
    )

def show_migrations():
    """Show migration history"""
    return run_command(
        ["alembic", "history", "--verbose"],
        "Showing migration history"
    )

def show_current():
    """Show current migration"""
    return run_command(
        ["alembic", "current"],
        "Showing current migration"
    )

def main():
    if len(sys.argv) < 2:
        print("""
🗄️  Database Migration Manager

Usage: python migrate.py <command> [args]

Commands:
  init                    - Initialize migrations (first time only)
  create <message>        - Create new migration
  upgrade                 - Apply all pending migrations  
  downgrade [revision]    - Downgrade to revision (default: base)
  history                 - Show migration history
  current                 - Show current migration
  
Examples:
  python migrate.py init
  python migrate.py create "Add user table"
  python migrate.py upgrade
  python migrate.py downgrade
  python migrate.py history
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Change to the backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if command == "init":
        success = init_migrations()
    elif command == "create":
        message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Auto migration"
        success = create_migration(message)
    elif command == "upgrade":
        success = upgrade_database()
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "base"
        success = downgrade_database(revision)
    elif command == "history":
        success = show_migrations()
    elif command == "current":
        success = show_current()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
    
    if success:
        print("✅ Command completed successfully!")
    else:
        print("❌ Command failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
