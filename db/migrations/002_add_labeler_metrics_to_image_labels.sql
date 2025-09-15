-- Migration: Add performance metrics and mode tracking to image_labels
-- Date: 2025-01-15
-- Purpose: Track labeler performance, costs, and execution modes

-- Add new columns to image_labels table
ALTER TABLE image_labels 
ADD COLUMN IF NOT EXISTS labeler_mode VARCHAR(20) DEFAULT 'production',
ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS api_cost_cents DECIMAL(10,4);

-- Add index for mode filtering
CREATE INDEX IF NOT EXISTS idx_image_labels_mode ON image_labels(labeler_mode);

-- Add indexes for performance queries
CREATE INDEX IF NOT EXISTS idx_image_labels_execution_time ON image_labels(execution_time_ms);
CREATE INDEX IF NOT EXISTS idx_image_labels_api_cost ON image_labels(api_cost_cents);

-- Update existing labels to have production mode
-- (only updates rows where labeler_mode is NULL, won't affect already set values)
UPDATE image_labels 
SET labeler_mode = 'production' 
WHERE labeler_mode IS NULL;

-- Add constraint for valid modes
-- Note: This will fail if there are any existing invalid values
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'valid_labeler_mode'
    ) THEN
        ALTER TABLE image_labels 
        ADD CONSTRAINT valid_labeler_mode 
        CHECK (labeler_mode IN ('production', 'shadow', 'experimental', 'deprecated'));
    END IF;
END $$;