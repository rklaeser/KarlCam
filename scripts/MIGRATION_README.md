# KarlCam PostgreSQL → Firestore Migration

This guide walks you through migrating all KarlCam data from PostgreSQL (staging + production) to a single Firestore instance.

## What Gets Migrated

- ✅ All webcams from both databases (deduplicated)
- ✅ All labeled images from staging (~X images)
- ✅ All labeled images from production (~Y images)
- ✅ System status and metadata
- ✅ Each label is tagged with `source_environment` (staging/production)

## Prerequisites

### 1. Install Dependencies

```bash
pip install firebase-admin google-cloud-firestore psycopg2-binary
```

### 2. Set Up Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project named `karlcam` (or use existing)
3. Go to **Project Settings** > **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file as `karlcam-firebase-key.json`

### 3. Set Up Environment Variables

Create or update your `.env` file:

```bash
# Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/karlcam-firebase-key.json"

# PostgreSQL databases
export STAGING_DATABASE_URL="postgresql://karlcam_staging:<PASSWORD>@localhost:5432/karlcam_staging"
export PRODUCTION_DATABASE_URL="postgresql://karlcam_production:<PASSWORD>@localhost:5432/karlcam_production"
```

Get the password:
```bash
gcloud secrets versions access latest --secret="karlcam-db-password" --project=karlcam
```

Or read from your `.env` file.

### 4. Start Cloud SQL Proxy

```bash
# Make sure proxy is running
make start-sql

# Or check if already running
lsof -i :5432
```

## Running the Migration

### Step 1: Test Connection

```bash
# Load environment variables
source .env  # or: export $(cat .env | xargs)

# Test Firestore connection
python3 -c "import firebase_admin; from firebase_admin import firestore; firebase_admin.initialize_app(); print('✓ Firestore connected')"

# Test PostgreSQL connections
psql "$STAGING_DATABASE_URL" -c "SELECT COUNT(*) FROM webcams;"
psql "$PRODUCTION_DATABASE_URL" -c "SELECT COUNT(*) FROM webcams;"
```

### Step 2: Run Migration

```bash
cd /Users/reed/Code/KarlCam
python scripts/migrate_postgres_to_firestore.py
```

The script will:
1. Show which databases will be migrated
2. Ask for confirmation
3. Migrate staging database first
4. Migrate production database second
5. Update system status
6. Verify migration

**Expected output:**
```
======================================================================
KarlCam PostgreSQL → Firestore Migration (Staging + Production)
======================================================================

Databases to migrate:
  ✓ Staging: localhost:5432/karlcam_staging
  ✓ Production: localhost:5432/karlcam_production

This will migrate ALL data from both databases into a single Firestore instance.
This consolidates staging and production data together.

Continue? (yes/no): yes

Connecting to Firestore...
✓ Connected to Firestore

======================================================================
MIGRATING STAGING DATABASE
======================================================================

=== Exporting Webcams from staging ===
  ✓ Created webcam: sutro-tower (Sutro Tower)
  ...
✓ staging: 12 new, 0 updated

=== Exporting Labels from staging ===
  ✓ Committed batch of 500 labels (total: 500)
  ...
✓ staging: Exported 847 labels

✓ Staging PostgreSQL connection closed

======================================================================
MIGRATING PRODUCTION DATABASE
======================================================================
...
```

### Step 3: Verify Migration

After migration completes, verify in Firebase Console:

1. Go to https://console.firebase.google.com/
2. Select your project
3. Navigate to **Firestore Database**
4. Check collections:
   - `webcams`: Should have 12 documents
   - `labels`: Should have ~1000+ documents
   - `system`: Should have 1 document (status)

Query examples in Console:
```
// Find all staging labels
labels where source_environment == "staging"

// Find labels for a specific camera
labels where camera_id == "sutro-tower" order by timestamp desc

// Find high confidence fog detections
labels where fog_score >= 70 and confidence >= 0.85
```

## Firestore Schema

### Collections

#### `webcams/`
```
{camera_id}/
  id: "sutro-tower"
  name: "Sutro Tower"
  latitude: 37.7558
  longitude: -122.4528
  url: "https://..."
  active: true
  camera_type: "static_url"
  created_at: timestamp
  updated_at: timestamp
```

#### `labels/`
```
{auto-generated-id}/
  camera_id: "sutro-tower"
  camera_name: "Sutro Tower"
  timestamp: timestamp
  image_filename: "sutro-tower_20250129_120000.jpg"
  image_url: "gs://karlcam-fog-data/raw_images/..."
  labeler_name: "gemini-2.0-flash"
  fog_score: 75
  fog_level: "Moderate Fog"
  confidence: 0.92
  reasoning: "Visible fog obscuring..."
  weather_conditions: ["fog", "overcast"]
  latitude: 37.7558
  longitude: -122.4528
  labeled_at: timestamp
  source_environment: "staging"  // NEW: tracks origin
  image_id_postgres: 12345       // For reference
  label_id_postgres: 67890
```

#### `system/status/`
```
{
  total_labels_migrated: 1234
  labels_from_staging: 847
  labels_from_production: 387
  migration_completed_at: timestamp
  migrated_from: "postgresql"
  source_databases: ["staging", "production"]
  karlcam_mode: 0
}
```

## Querying Firestore

### Python Example

```python
from firebase_admin import firestore

db = firestore.client()

# Get latest label for each camera
cameras = db.collection('labels') \
    .where('camera_id', '==', 'sutro-tower') \
    .order_by('timestamp', direction=firestore.Query.DESCENDING) \
    .limit(1) \
    .stream()

for label in cameras:
    print(label.to_dict())

# Get all staging labels
staging_labels = db.collection('labels') \
    .where('source_environment', '==', 'staging') \
    .stream()

# Count total labels
labels_count = len(list(db.collection('labels').stream()))
```

### Using SvelteKit

```typescript
import { getFirestore, collection, query, where, orderBy, limit, getDocs } from 'firebase/firestore';

const db = getFirestore();

// Get latest conditions for all cameras
const webcams = await getDocs(collection(db, 'webcams'));
const latestConditions = [];

for (const webcam of webcams.docs) {
  const labelsQuery = query(
    collection(db, 'labels'),
    where('camera_id', '==', webcam.id),
    orderBy('timestamp', 'desc'),
    limit(1)
  );

  const snapshot = await getDocs(labelsQuery);
  if (!snapshot.empty) {
    latestConditions.push(snapshot.docs[0].data());
  }
}
```

## Troubleshooting

### Error: "GOOGLE_APPLICATION_CREDENTIALS not set"
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/karlcam-firebase-key.json"
```

### Error: "No database URLs provided"
```bash
export STAGING_DATABASE_URL="postgresql://..."
export PRODUCTION_DATABASE_URL="postgresql://..."
```

### Error: "could not connect to server"
```bash
# Start Cloud SQL Proxy
make start-sql

# Or check if running
lsof -i :5432
```

### Error: "Permission denied" in Firestore
Make sure your Firebase service account has:
- Cloud Datastore User role
- Firebase Admin SDK permissions

### Migration takes too long
The script processes in batches of 500. For ~1000 labels, expect 2-3 minutes.

## Next Steps

After successful migration:

1. ✅ **Test queries** - Verify data in Firebase Console
2. ✅ **Update collector** - Write new labels to Firestore instead of PostgreSQL
3. ✅ **Update frontend** - Read from Firestore instead of API → PostgreSQL
4. ✅ **Export to LabelBox** - Use Firestore data for ML training
5. ✅ **Shut down Cloud SQL** - Save $50-100/month!

## Rollback Plan

If something goes wrong:

1. **Data is still in PostgreSQL** - Original data is untouched
2. **Delete Firestore collections**:
   ```bash
   # In Firebase Console: Firestore Database → Delete collection
   ```
3. **Re-run migration** after fixing issues

## Cost Estimates

### Before Migration
- Cloud SQL: $50-100/month
- Cloud Storage: $1-5/month
- **Total: $51-105/month**

### After Migration
- Firestore Free Tier: 50k reads/20k writes per day (likely sufficient)
- Cloud Storage: $1-5/month
- **Total: $1-5/month (or $0-5/month if within free tier)**

**Savings: ~$50-100/month** 💰
