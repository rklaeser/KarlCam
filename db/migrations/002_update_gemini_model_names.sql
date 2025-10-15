-- Migration: Update Gemini model names to use latest API version
-- Date: 2025-10-14
-- Purpose: Fix Gemini API 404 errors by updating model names to valid versions
-- Issue: Production labeling failing with "models/gemini-1.5-flash is not found for API version v1beta"

-- Update existing Gemini labeler configurations to use the correct model name
UPDATE labeler_config 
SET 
    config = jsonb_set(config, '{model}', '"gemini-1.5-flash-latest"'::jsonb),
    updated_at = NOW()
WHERE 
    name IN ('gemini', 'gemini_masked')
    AND config->>'model' = 'gemini-1.5-flash';

-- Verify the update was successful
SELECT 
    name, 
    mode, 
    enabled,
    config->>'model' as model_name,
    updated_at
FROM labeler_config 
WHERE name IN ('gemini', 'gemini_masked')
ORDER BY name;