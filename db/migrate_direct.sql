-- Direct SQL migration from old karlcam to new karlcam_v2
-- Run this against the karlcam_v2 database

-- Connect to v2 database first
\c karlcam_v2;

-- Clear existing data (careful!)
TRUNCATE TABLE image_collections RESTART IDENTITY CASCADE;
TRUNCATE TABLE image_labels RESTART IDENTITY;

-- Migrate image collections (just the collection data, no labels)
INSERT INTO image_collections (id, collection_run_id, webcam_id, timestamp, image_filename, cloud_storage_path, created_at)
SELECT id, collection_run_id, webcam_id, timestamp, image_filename, cloud_storage_path, created_at
FROM dblink('dbname=karlcam host=/cloudsql/karlcam:us-central1:karlcam-db user=karlcam password=Tabudas38',
           'SELECT id, collection_run_id, webcam_id, timestamp, image_filename, cloud_storage_path, created_at FROM image_collections ORDER BY id')
AS t(id int, collection_run_id int, webcam_id varchar, timestamp timestamptz, image_filename varchar, cloud_storage_path varchar, created_at timestamptz);

-- Reset sequence
SELECT setval('image_collections_id_seq', COALESCE((SELECT MAX(id) FROM image_collections), 0) + 1, false);

-- Migrate labels (extract from old image_collections labeling fields)  
INSERT INTO image_labels (image_id, labeler_name, labeler_version, fog_score, fog_level, confidence, reasoning, visibility_estimate, weather_conditions, label_data, created_at)
SELECT id, 'gemini_migrated', '1.0', fog_score, fog_level, confidence, reasoning, visibility_estimate, 
       CASE WHEN weather_conditions IS NOT NULL THEN weather_conditions::jsonb ELSE NULL END,
       NULL, NOW()
FROM dblink('dbname=karlcam host=/cloudsql/karlcam:us-central1:karlcam-db user=karlcam password=Tabudas38',
           'SELECT id, fog_score, fog_level, confidence, reasoning, visibility_estimate, weather_conditions FROM image_collections WHERE fog_score IS NOT NULL OR fog_level IS NOT NULL ORDER BY id')
AS t(id int, fog_score float, fog_level varchar, confidence float, reasoning text, visibility_estimate varchar, weather_conditions jsonb);

-- Verification
SELECT 'Images in old DB' as metric, count(*) as count FROM dblink('dbname=karlcam host=/cloudsql/karlcam:us-central1:karlcam-db user=karlcam password=Tabudas38', 'SELECT id FROM image_collections') AS t(id int)
UNION ALL
SELECT 'Images in new DB', count(*) FROM image_collections
UNION ALL  
SELECT 'Labels in old DB', count(*) FROM dblink('dbname=karlcam host=/cloudsql/karlcam:us-central1:karlcam-db user=karlcam password=Tabudas38', 'SELECT id FROM image_collections WHERE fog_score IS NOT NULL OR fog_level IS NOT NULL') AS t(id int)
UNION ALL
SELECT 'Labels in new DB', count(*) FROM image_labels;

-- Show sample of migrated data
SELECT 'Sample migrated images:' as info;
SELECT ic.id, ic.webcam_id, ic.timestamp, il.fog_score, il.fog_level 
FROM image_collections ic 
LEFT JOIN image_labels il ON ic.id = il.image_id 
ORDER BY ic.timestamp DESC 
LIMIT 5;

\echo 'Migration completed! Check the counts above to verify.'