-- KarlCam Database Schema
-- PostgreSQL schema for separated collection and labeling architecture

-- Webcams configuration table
CREATE TABLE IF NOT EXISTS webcams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    video_url TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Collection runs table
CREATE TABLE IF NOT EXISTS collection_runs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    total_images INTEGER DEFAULT 0,
    successful_images INTEGER DEFAULT 0,
    failed_images INTEGER DEFAULT 0,
    summary_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Image collections table (raw collected images without labels)
CREATE TABLE IF NOT EXISTS image_collections (
    id SERIAL PRIMARY KEY,
    collection_run_id INTEGER REFERENCES collection_runs(id),
    webcam_id VARCHAR(50) REFERENCES webcams(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    cloud_storage_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Image labels table (multiple labeling techniques per image)
CREATE TABLE IF NOT EXISTS image_labels (
    id SERIAL PRIMARY KEY,
    image_id INTEGER REFERENCES image_collections(id) ON DELETE CASCADE,
    labeler_name VARCHAR(100) NOT NULL,
    labeler_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    
    -- Core labeling results
    fog_score FLOAT,
    fog_level VARCHAR(50),
    confidence FLOAT,
    reasoning TEXT,
    visibility_estimate VARCHAR(100),
    weather_conditions JSONB DEFAULT '[]',
    
    -- Full label data for flexibility and new techniques
    label_data JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fog_score_range CHECK (fog_score >= 0 AND fog_score <= 100),
    CONSTRAINT confidence_range CHECK (confidence >= 0 AND confidence <= 1.0),
    CONSTRAINT valid_fog_level CHECK (fog_level IN ('Clear', 'Light Fog', 'Moderate Fog', 'Heavy Fog', 'Very Heavy Fog', 'Unknown')),
    
    -- Unique constraint: one label per labeler version per image
    UNIQUE(image_id, labeler_name, labeler_version)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_webcams_active ON webcams(active);
CREATE INDEX IF NOT EXISTS idx_collection_runs_timestamp ON collection_runs(timestamp);

CREATE INDEX IF NOT EXISTS idx_image_collections_webcam_id ON image_collections(webcam_id);
CREATE INDEX IF NOT EXISTS idx_image_collections_timestamp ON image_collections(timestamp);
CREATE INDEX IF NOT EXISTS idx_image_collections_collection_run_id ON image_collections(collection_run_id);
CREATE INDEX IF NOT EXISTS idx_image_collections_filename ON image_collections(image_filename);

CREATE INDEX IF NOT EXISTS idx_image_labels_image_id ON image_labels(image_id);
CREATE INDEX IF NOT EXISTS idx_image_labels_labeler ON image_labels(labeler_name, labeler_version);
CREATE INDEX IF NOT EXISTS idx_image_labels_fog_score ON image_labels(fog_score);
CREATE INDEX IF NOT EXISTS idx_image_labels_confidence ON image_labels(confidence);
CREATE INDEX IF NOT EXISTS idx_image_labels_created_at ON image_labels(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at for webcams
DROP TRIGGER IF EXISTS update_webcams_updated_at ON webcams;
CREATE TRIGGER update_webcams_updated_at BEFORE UPDATE ON webcams
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for convenience

-- View to get images with their latest labels
CREATE OR REPLACE VIEW image_summary AS
SELECT 
    ic.id as image_id,
    ic.webcam_id,
    ic.timestamp,
    ic.image_filename,
    ic.cloud_storage_path,
    COUNT(il.id) as label_count,
    ARRAY_AGG(il.labeler_name || '_v' || il.labeler_version) FILTER (WHERE il.id IS NOT NULL) as labelers
FROM image_collections ic
LEFT JOIN image_labels il ON ic.id = il.image_id
GROUP BY ic.id, ic.webcam_id, ic.timestamp, ic.image_filename, ic.cloud_storage_path;

-- View to compare labeling techniques
CREATE OR REPLACE VIEW label_comparison AS
SELECT 
    ic.image_filename,
    ic.webcam_id,
    ic.timestamp,
    il.labeler_name,
    il.labeler_version,
    il.fog_score,
    il.fog_level,
    il.confidence,
    il.created_at as labeled_at
FROM image_collections ic
JOIN image_labels il ON ic.id = il.image_id
ORDER BY ic.timestamp DESC, il.labeler_name;