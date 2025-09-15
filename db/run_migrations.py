#!/usr/bin/env python3
"""
Run database migrations in order
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from db.connection import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_all_migrations():
    """Run all migrations in the migrations directory"""
    migrations_dir = Path(__file__).parent / 'migrations'
    
    # Create migrations directory if it doesn't exist
    migrations_dir.mkdir(exist_ok=True)
    
    # Get all .sql files in migrations directory
    migration_files = sorted(migrations_dir.glob('*.sql'))
    
    if not migration_files:
        logger.info("No migration files found")
        return
    
    logger.info(f"Found {len(migration_files)} migration files")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for migration_file in migration_files:
                logger.info(f"Running migration: {migration_file.name}")
                
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()
                
                try:
                    cur.execute(migration_sql)
                    conn.commit()
                    logger.info(f"✅ {migration_file.name} completed successfully")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"❌ {migration_file.name} failed: {e}")
                    raise


def run_specific_migration(migration_name):
    """Run a specific migration by name"""
    migrations_dir = Path(__file__).parent / 'migrations'
    
    # Find the migration file
    migration_file = migrations_dir / f"{migration_name}.sql"
    if not migration_file.exists():
        # Try with just the filename if it already has .sql
        migration_file = migrations_dir / migration_name
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_name}")
            logger.info(f"Available migrations in {migrations_dir}:")
            for f in sorted(migrations_dir.glob('*.sql')):
                logger.info(f"  - {f.name}")
            return False
    
    logger.info(f"Running specific migration: {migration_file.name}")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            try:
                cur.execute(migration_sql)
                conn.commit()
                logger.info(f"✅ {migration_file.name} completed successfully")
                return True
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ {migration_file.name} failed: {e}")
                raise


def list_migrations():
    """List all available migrations"""
    migrations_dir = Path(__file__).parent / 'migrations'
    migration_files = sorted(migrations_dir.glob('*.sql'))
    
    if not migration_files:
        logger.info("No migration files found")
        return
    
    logger.info(f"Available migrations in {migrations_dir}:")
    for migration_file in migration_files:
        logger.info(f"  - {migration_file.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument('--migration', '-m', help='Run specific migration by name (e.g., 003_create_performance_analytics_views)')
    parser.add_argument('--list', '-l', action='store_true', help='List available migrations')
    
    args = parser.parse_args()
    
    try:
        if args.list:
            list_migrations()
        elif args.migration:
            success = run_specific_migration(args.migration)
            if success:
                logger.info("🎉 Migration completed successfully!")
            else:
                sys.exit(1)
        else:
            run_all_migrations()
            logger.info("🎉 All migrations completed successfully!")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)