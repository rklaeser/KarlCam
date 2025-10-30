#!/usr/bin/env python3
"""
Migrate KarlCam data from PostgreSQL to Firestore

This script:
1. Exports all webcams from PostgreSQL (staging + production) to Firestore
2. Exports all labeled images (image_collections + image_labels) to Firestore
3. Consolidates staging and production data into single Firestore instance
4. Preserves all metadata and tracks source environment
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import firebase_admin
from firebase_admin import credentials, firestore
import psycopg2
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def get_pg_connection(database_url: str):
    """Connect to PostgreSQL database"""
    return psycopg2.connect(database_url)


def get_environment_name(database_url: str) -> str:
    """Extract environment name from database URL"""
    parsed = urlparse(database_url)
    db_name = parsed.path.strip('/')

    if 'staging' in db_name:
        return 'staging'
    elif 'production' in db_name:
        return 'production'
    else:
        return 'unknown'


def initialize_firestore() -> firestore.Client:
    """Initialize Firebase Admin SDK"""
    # Check if already initialized
    try:
        app = firebase_admin.get_app()
    except ValueError:
        # Initialize with default credentials and project
        app = firebase_admin.initialize_app(options={
            'projectId': 'karlcam'
        })

    # Use the named database "karlcam-firestore" (not default)
    return firestore.client(database_id='karlcam-firestore')


def export_webcams(pg_conn, fs_client: firestore.Client, environment: str) -> Dict[str, str]:
    """
    Export webcams from PostgreSQL to Firestore
    Merges with existing webcams (doesn't duplicate)
    Returns mapping of webcam_id -> firestore_doc_id
    """
    print(f"\n=== Exporting Webcams from {environment} ===")

    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT id, name, url, video_url, latitude, longitude,
               description, active, camera_type, discovery_metadata,
               created_at, updated_at
        FROM webcams
        ORDER BY id
    """)

    webcams_ref = fs_client.collection('webcams')
    webcam_mapping = {}
    count_new = 0
    count_updated = 0

    for row in cursor.fetchall():
        webcam_id = row[0]

        # Create Firestore document
        doc_data = {
            'id': row[0],
            'name': row[1],
            'url': row[2],
            'video_url': row[3],
            'latitude': float(row[4]) if row[4] else None,
            'longitude': float(row[5]) if row[5] else None,
            'description': row[6],
            'active': row[7] if row[7] is not None else True,
            'camera_type': row[8] or 'static_url',
            'discovery_metadata': row[9],
            'created_at': row[10] or datetime.utcnow(),
            'updated_at': row[11] or datetime.utcnow(),
        }

        # Remove None values
        doc_data = {k: v for k, v in doc_data.items() if v is not None}

        # Check if webcam already exists
        doc_ref = webcams_ref.document(webcam_id)
        existing_doc = doc_ref.get()

        if existing_doc.exists:
            # Merge/update existing webcam
            doc_ref.set(doc_data, merge=True)
            count_updated += 1
            print(f"  ↻ Updated webcam: {webcam_id} ({row[1]})")
        else:
            # Create new webcam
            doc_ref.set(doc_data)
            count_new += 1
            print(f"  ✓ Created webcam: {webcam_id} ({row[1]})")

        webcam_mapping[webcam_id] = webcam_id

    cursor.close()
    print(f"✓ {environment}: {count_new} new, {count_updated} updated")
    return webcam_mapping


def export_labels(pg_conn, fs_client: firestore.Client, webcam_mapping: Dict[str, str], environment: str) -> int:
    """
    Export labeled images from PostgreSQL to Firestore
    Joins image_collections with image_labels
    Tracks source environment for all labels
    """
    print(f"\n=== Exporting Labels from {environment} ===")

    cursor = pg_conn.cursor()

    # Query joins image_collections with image_labels
    cursor.execute("""
        SELECT
            ic.id as image_id,
            ic.webcam_id,
            ic.timestamp,
            ic.image_filename,
            ic.cloud_storage_path,
            ic.created_at,
            il.id as label_id,
            il.labeler_name,
            il.labeler_version,
            il.fog_score,
            il.fog_level,
            il.confidence,
            il.reasoning,
            il.visibility_estimate,
            il.weather_conditions,
            il.label_data,
            il.created_at as labeled_at,
            w.name as camera_name,
            w.latitude,
            w.longitude
        FROM image_collections ic
        INNER JOIN image_labels il ON ic.id = il.image_id
        LEFT JOIN webcams w ON ic.webcam_id = w.id
        ORDER BY ic.timestamp DESC
    """)

    labels_ref = fs_client.collection('labels')
    count = 0
    skipped = 0
    batch = fs_client.batch()
    batch_count = 0
    BATCH_SIZE = 500  # Firestore batch limit

    for row in cursor.fetchall():
        image_id = row[0]
        webcam_id = row[1]
        timestamp = row[2]
        image_filename = row[3]
        cloud_storage_path = row[4]
        image_created_at = row[5]

        label_id = row[6]
        labeler_name = row[7]
        labeler_version = row[8]
        fog_score = row[9]
        fog_level = row[10]
        confidence = row[11]
        reasoning = row[12]
        visibility_estimate = row[13]
        weather_conditions = row[14]
        label_data = row[15]
        labeled_at = row[16]

        camera_name = row[17]
        latitude = row[18]
        longitude = row[19]

        # Skip if no webcam found
        if webcam_id not in webcam_mapping:
            print(f"  ⚠ Skipping image {image_id}: webcam {webcam_id} not found")
            skipped += 1
            continue

        # Create Firestore document with auto-generated ID to avoid conflicts
        # between staging and production
        doc_data = {
            'camera_id': webcam_id,
            'camera_name': camera_name or webcam_id,
            'timestamp': timestamp or datetime.utcnow(),
            'image_filename': image_filename,
            'image_url': cloud_storage_path or f"gs://karlcam-fog-data/raw_images/{image_filename}",
            'labeler_name': labeler_name,
            'labeler_version': labeler_version or '1.0',
            'fog_score': int(fog_score) if fog_score is not None else None,
            'fog_level': fog_level,
            'confidence': float(confidence) if confidence is not None else None,
            'reasoning': reasoning,
            'visibility_estimate': visibility_estimate,
            'weather_conditions': weather_conditions or [],
            'label_data': label_data,
            'latitude': float(latitude) if latitude else None,
            'longitude': float(longitude) if longitude else None,
            'labeled_at': labeled_at or image_created_at or datetime.utcnow(),
            'source_environment': environment,  # Track which DB this came from
            'image_id_postgres': image_id,  # Keep reference to old ID
            'label_id_postgres': label_id,
        }

        # Remove None values
        doc_data = {k: v for k, v in doc_data.items() if v is not None}

        # Add to batch with auto-generated ID
        doc_ref = labels_ref.document()  # Auto-generate unique ID
        batch.set(doc_ref, doc_data)
        batch_count += 1
        count += 1

        # Commit batch if at limit
        if batch_count >= BATCH_SIZE:
            batch.commit()
            print(f"  ✓ Committed batch of {batch_count} labels (total: {count})")
            batch = fs_client.batch()
            batch_count = 0

    # Commit remaining batch
    if batch_count > 0:
        batch.commit()
        print(f"  ✓ Committed final batch of {batch_count} labels")

    cursor.close()
    print(f"✓ {environment}: Exported {count} labels")
    if skipped > 0:
        print(f"⚠ {environment}: Skipped {skipped} labels (missing webcam references)")

    return count


def update_system_status(fs_client: firestore.Client, total_staging: int, total_production: int):
    """
    Update system status in Firestore with migration summary
    """
    print("\n=== Updating System Status ===")

    # Create system status document
    system_ref = fs_client.collection('system').document('status')
    system_ref.set({
        'total_labels_migrated': total_staging + total_production,
        'labels_from_staging': total_staging,
        'labels_from_production': total_production,
        'migration_completed_at': datetime.utcnow(),
        'migrated_from': 'postgresql',
        'source_databases': ['staging', 'production'],
        'karlcam_mode': 0,  # Default to day mode
    })

    print(f"✓ System status updated (staging: {total_staging}, production: {total_production})")


def verify_migration(fs_client: firestore.Client):
    """
    Verify the migration by counting documents
    """
    print("\n=== Verifying Migration ===")

    webcams_count = len(list(fs_client.collection('webcams').stream()))
    labels_count = len(list(fs_client.collection('labels').stream()))

    print(f"  Webcams in Firestore: {webcams_count}")
    print(f"  Labels in Firestore: {labels_count}")

    # Show sample label
    sample_label = next(fs_client.collection('labels').limit(1).stream(), None)
    if sample_label:
        print(f"\n  Sample label document:")
        data = sample_label.to_dict()
        for key, value in list(data.items())[:5]:
            print(f"    {key}: {value}")

    return webcams_count, labels_count


def main():
    """Main migration process"""
    print("=" * 70)
    print("KarlCam PostgreSQL → Firestore Migration (Staging + Production)")
    print("=" * 70)

    # Get database URLs from environment or .env file
    staging_url = os.getenv('STAGING_DATABASE_URL')
    production_url = os.getenv('PRODUCTION_DATABASE_URL')

    if not staging_url and not production_url:
        print("❌ ERROR: No database URLs provided")
        print("\nSet environment variables:")
        print("  export STAGING_DATABASE_URL='postgresql://karlcam_staging:password@localhost:5432/karlcam_staging'")
        print("  export PRODUCTION_DATABASE_URL='postgresql://karlcam_production:password@localhost:5432/karlcam_production'")
        print("\nOr use .env file with these variables")
        sys.exit(1)

    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("⚠️  WARNING: GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   Attempting to use default credentials...")

    # Show what will be migrated
    print("\nDatabases to migrate:")
    if staging_url:
        print(f"  ✓ Staging: {staging_url.split('@')[1] if '@' in staging_url else 'configured'}")
    if production_url:
        print(f"  ✓ Production: {production_url.split('@')[1] if '@' in production_url else 'configured'}")

    # Confirm before proceeding
    print("\nThis will migrate ALL data from both databases into a single Firestore instance.")
    print("This consolidates staging and production data together.")
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)

    staging_conn = None
    production_conn = None
    total_staging_labels = 0
    total_production_labels = 0

    try:
        # Initialize Firestore
        print("\nConnecting to Firestore...")
        fs_client = initialize_firestore()
        print("✓ Connected to Firestore")

        # Migrate Staging Database
        if staging_url:
            print("\n" + "=" * 70)
            print("MIGRATING STAGING DATABASE")
            print("=" * 70)

            staging_conn = get_pg_connection(staging_url)
            print("✓ Connected to staging PostgreSQL")

            staging_env = get_environment_name(staging_url)
            webcam_mapping_staging = export_webcams(staging_conn, fs_client, staging_env)
            total_staging_labels = export_labels(staging_conn, fs_client, webcam_mapping_staging, staging_env)

            staging_conn.close()
            print("✓ Staging PostgreSQL connection closed")

        # Migrate Production Database
        if production_url:
            print("\n" + "=" * 70)
            print("MIGRATING PRODUCTION DATABASE")
            print("=" * 70)

            production_conn = get_pg_connection(production_url)
            print("✓ Connected to production PostgreSQL")

            production_env = get_environment_name(production_url)
            webcam_mapping_production = export_webcams(production_conn, fs_client, production_env)
            total_production_labels = export_labels(production_conn, fs_client, webcam_mapping_production, production_env)

            production_conn.close()
            print("✓ Production PostgreSQL connection closed")

        # Update system status
        update_system_status(fs_client, total_staging_labels, total_production_labels)

        # Verify
        webcams_count, labels_count = verify_migration(fs_client)

        print("\n" + "=" * 70)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n  Webcams in Firestore: {webcams_count}")
        print(f"  Total labels migrated: {labels_count}")
        print(f"    - From staging: {total_staging_labels}")
        print(f"    - From production: {total_production_labels}")
        print("\nNext steps:")
        print("  1. Review data in Firebase Console")
        print("  2. Test queries: query labels by 'source_environment' field")
        print("  3. Update collector/labeler to write to Firestore")
        print("  4. Update frontend to read from Firestore")
        print("  5. Once verified, shut down Cloud SQL (save ~$50-100/month!)")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: Migration failed")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if staging_conn and not staging_conn.closed:
            staging_conn.close()
        if production_conn and not production_conn.closed:
            production_conn.close()


if __name__ == "__main__":
    main()
