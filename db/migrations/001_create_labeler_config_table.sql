-- Migration: Create labeler configuration table
-- Date: 2025-01-15
-- Purpose: Support dynamic labeler configuration and mode management

-- Create labeler configuration table
CREATE TABLE IF NOT EXISTS labeler_config (
    name VARCHAR(50) PRIMARY KEY,
    mode VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    version VARCHAR(20),
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_config_mode CHECK (mode IN ('production', 'shadow', 'experimental', 'deprecated'))
);

-- Add trigger to automatically update updated_at for labeler_config
DROP TRIGGER IF EXISTS update_labeler_config_updated_at ON labeler_config;
CREATE TRIGGER update_labeler_config_updated_at BEFORE UPDATE ON labeler_config
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_labeler_config_mode ON labeler_config(mode);
CREATE INDEX IF NOT EXISTS idx_labeler_config_enabled ON labeler_config(enabled);

-- Insert default configurations for existing labelers
INSERT INTO labeler_config (name, mode, enabled, version, config) 
VALUES 
    ('gemini', 'production', true, '1.0', '{"model": "gemini-1.5-flash-latest", "temperature": 0.1}'),
    ('gemini_masked', 'shadow', true, '1.0', '{"model": "gemini-1.5-flash-latest", "temperature": 0.1, "use_mask": true}')
ON CONFLICT (name) DO NOTHING;