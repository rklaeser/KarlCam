-- Migration: Remove labeler configuration table
-- Date: 2025-10-15
-- Purpose: Simplify configuration management by removing database-based labeler config

-- Drop indexes first
DROP INDEX IF EXISTS idx_labeler_config_mode;
DROP INDEX IF EXISTS idx_labeler_config_enabled;

-- Drop trigger
DROP TRIGGER IF EXISTS update_labeler_config_updated_at ON labeler_config;

-- Drop dependent views that reference labeler_config
DROP VIEW IF EXISTS labeler_performance_summary CASCADE;
DROP VIEW IF EXISTS labeler_reliability_analysis CASCADE;
DROP VIEW IF EXISTS labeler_daily_performance CASCADE;
DROP VIEW IF EXISTS labeler_agreement_analysis CASCADE;

-- Drop the table
DROP TABLE IF EXISTS labeler_config CASCADE;

-- Recreate performance views without labeler_config dependency
-- These views now get labeler information directly from image_labels table

CREATE OR REPLACE VIEW labeler_performance_summary AS
SELECT 
    il.labeler_name,
    'production' as labeler_mode,  -- Mode is now determined by environment
    COUNT(*) as total_executions,
    AVG(il.execution_time_ms) as avg_execution_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY il.execution_time_ms) as median_execution_time_ms,
    MIN(il.execution_time_ms) as min_execution_time_ms,
    MAX(il.execution_time_ms) as max_execution_time_ms,
    AVG(il.confidence) as avg_confidence,
    AVG(il.fog_score) as avg_fog_score,
    SUM(il.api_cost_cents) as total_cost_cents,
    AVG(il.api_cost_cents) as avg_cost_cents,
    COUNT(CASE WHEN il.fog_level = 'Clear' THEN 1 END) as clear_count,
    COUNT(CASE WHEN il.fog_level = 'Light Fog' THEN 1 END) as light_fog_count,
    COUNT(CASE WHEN il.fog_level = 'Moderate Fog' THEN 1 END) as moderate_fog_count,
    COUNT(CASE WHEN il.fog_level = 'Heavy Fog' THEN 1 END) as heavy_fog_count,
    COUNT(CASE WHEN il.fog_level = 'Very Heavy Fog' THEN 1 END) as very_heavy_fog_count,
    MIN(il.created_at) as first_execution,
    MAX(il.created_at) as last_execution,
    COUNT(CASE WHEN il.created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as executions_last_24h
FROM image_labels il
GROUP BY il.labeler_name;

CREATE OR REPLACE VIEW labeler_daily_performance AS
SELECT 
    DATE(il.created_at) as execution_date,
    il.labeler_name,
    'production' as labeler_mode,  -- Mode is now determined by environment
    COUNT(*) as daily_executions,
    AVG(il.execution_time_ms) as avg_execution_time_ms,
    AVG(il.api_cost_cents) as avg_cost_cents,
    AVG(il.confidence) as avg_confidence,
    SUM(il.api_cost_cents) as total_daily_cost_cents
FROM image_labels il
GROUP BY DATE(il.created_at), il.labeler_name
ORDER BY execution_date DESC, il.labeler_name;

CREATE OR REPLACE VIEW labeler_agreement_analysis AS
WITH label_aggregates AS (
    SELECT 
        il.image_id,
        ic.webcam_id,
        ic.timestamp as image_timestamp,
        COUNT(DISTINCT il.labeler_name) as total_labelers_run,
        AVG(il.fog_score) as avg_fog_score,
        STDDEV(il.fog_score) as fog_score_stddev,
        MAX(il.fog_score) - MIN(il.fog_score) as fog_score_range,
        MODE() WITHIN GROUP (ORDER BY il.fog_level) as consensus_fog_level
    FROM image_labels il
    JOIN image_collections ic ON il.image_id = ic.id
    GROUP BY il.image_id, ic.webcam_id, ic.timestamp
),
primary_labels AS (
    SELECT DISTINCT ON (il.image_id)
        il.image_id,
        il.labeler_name as primary_labeler,
        il.fog_score as primary_fog_score,
        il.fog_level as primary_fog_level
    FROM image_labels il
    ORDER BY il.image_id, il.confidence DESC
)
SELECT 
    la.image_id,
    la.webcam_id,
    la.image_timestamp,
    pl.primary_labeler,
    pl.primary_fog_score,
    pl.primary_fog_level,
    la.fog_score_range as fog_score_disagreement,
    la.total_labelers_run
FROM label_aggregates la
LEFT JOIN primary_labels pl ON la.image_id = pl.image_id
WHERE la.total_labelers_run > 1;

-- Note: Performance monitoring remains intact
-- Configuration is now managed through environment variables