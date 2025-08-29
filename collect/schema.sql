-- KarlCam Database Schema
-- PostgreSQL schema for webcam collection data

-- Webcams configuration table
CREATE TABLE IF NOT EXISTS webcams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
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
    needs_review_count INTEGER DEFAULT 0,
    summary_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Simplified image collections table (Gemini-only approach)
CREATE TABLE IF NOT EXISTS image_collections (
    id SERIAL PRIMARY KEY,
    collection_run_id INTEGER REFERENCES collection_runs(id),
    webcam_id VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE,
    image_filename VARCHAR(255),
    
    -- Gemini scoring results
    fog_score FLOAT,
    fog_level VARCHAR(50),
    confidence FLOAT,
    reasoning TEXT,
    visibility_estimate VARCHAR(50),
    weather_conditions JSONB DEFAULT '[]',
    
    -- Status and storage
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    cloud_storage_path VARCHAR(500),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fog_score_range CHECK (fog_score >= 0 AND fog_score <= 100),
    CONSTRAINT confidence_range CHECK (confidence >= 0 AND confidence <= 1.0),
    CONSTRAINT valid_fog_level CHECK (fog_level IN ('Clear', 'Light Fog', 'Moderate Fog', 'Heavy Fog', 'Very Heavy Fog', 'Error', 'Unknown')),
    CONSTRAINT valid_status CHECK (status IN ('success', 'error', 'pending'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_image_collections_webcam_id ON image_collections(webcam_id);
CREATE INDEX IF NOT EXISTS idx_image_collections_timestamp ON image_collections(timestamp);
CREATE INDEX IF NOT EXISTS idx_image_collections_confidence ON image_collections(confidence);
CREATE INDEX IF NOT EXISTS idx_image_collections_fog_score ON image_collections(fog_score);
CREATE INDEX IF NOT EXISTS idx_image_collections_collection_run_id ON image_collections(collection_run_id);
CREATE INDEX IF NOT EXISTS idx_collection_runs_timestamp ON collection_runs(timestamp);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at for webcams
CREATE TRIGGER update_webcams_updated_at BEFORE UPDATE ON webcams
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();