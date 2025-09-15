-- Migration: Create performance analytics views for admin API
-- Date: 2025-01-15
-- Purpose: Support performance monitoring and labeler comparison APIs

-- 1. Labeler Performance Summary View
CREATE OR REPLACE VIEW labeler_performance_summary AS
SELECT 
    il.labeler_name,
    il.labeler_version,
    il.labeler_mode,
    lc.enabled as currently_enabled,
    lc.config as labeler_config,
    
    -- Execution metrics
    COUNT(*) as total_executions,
    AVG(il.execution_time_ms) as avg_execution_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY il.execution_time_ms) as median_execution_time_ms,
    MIN(il.execution_time_ms) as min_execution_time_ms,
    MAX(il.execution_time_ms) as max_execution_time_ms,
    STDDEV(il.execution_time_ms) as stddev_execution_time_ms,
    
    -- Cost metrics
    AVG(il.api_cost_cents) as avg_cost_cents,
    SUM(il.api_cost_cents) as total_cost_cents,
    
    -- Quality metrics
    AVG(il.confidence) as avg_confidence,
    STDDEV(il.confidence) as stddev_confidence,
    MIN(il.confidence) as min_confidence,
    MAX(il.confidence) as max_confidence,
    
    -- Fog score distribution
    AVG(il.fog_score) as avg_fog_score,
    STDDEV(il.fog_score) as stddev_fog_score,
    
    -- Fog level distribution
    COUNT(CASE WHEN il.fog_level = 'Clear' THEN 1 END) as clear_count,
    COUNT(CASE WHEN il.fog_level = 'Light Fog' THEN 1 END) as light_fog_count,
    COUNT(CASE WHEN il.fog_level = 'Moderate Fog' THEN 1 END) as moderate_fog_count,
    COUNT(CASE WHEN il.fog_level = 'Heavy Fog' THEN 1 END) as heavy_fog_count,
    COUNT(CASE WHEN il.fog_level = 'Very Heavy Fog' THEN 1 END) as very_heavy_fog_count,
    
    -- Time range
    MIN(il.created_at) as first_execution,
    MAX(il.created_at) as last_execution,
    
    -- Recent activity (last 24 hours)
    COUNT(CASE WHEN il.created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as executions_last_24h,
    AVG(CASE WHEN il.created_at > NOW() - INTERVAL '24 hours' THEN il.execution_time_ms END) as avg_time_last_24h
    
FROM image_labels il
LEFT JOIN labeler_config lc ON il.labeler_name = lc.name
GROUP BY il.labeler_name, il.labeler_version, il.labeler_mode, lc.enabled, lc.config;

-- 2. Daily Performance Trends View
CREATE OR REPLACE VIEW labeler_daily_performance AS
SELECT 
    il.labeler_name,
    il.labeler_mode,
    DATE(il.created_at) as execution_date,
    
    COUNT(*) as daily_executions,
    AVG(il.execution_time_ms) as avg_execution_time_ms,
    AVG(il.api_cost_cents) as avg_cost_cents,
    AVG(il.confidence) as avg_confidence,
    AVG(il.fog_score) as avg_fog_score,
    
    -- Performance percentiles
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY il.execution_time_ms) as median_execution_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY il.execution_time_ms) as p95_execution_time_ms,
    
    SUM(il.api_cost_cents) as total_daily_cost_cents
    
FROM image_labels il
WHERE il.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY il.labeler_name, il.labeler_mode, DATE(il.created_at)
ORDER BY execution_date DESC, il.labeler_name;

-- 3. Labeler Agreement Analysis View
CREATE OR REPLACE VIEW labeler_agreement_analysis AS
SELECT 
    ic.id as image_id,
    ic.webcam_id,
    ic.timestamp as image_timestamp,
    
    -- Primary labeler (first production labeler alphabetically)
    MIN(CASE WHEN il.labeler_mode = 'production' THEN il.labeler_name END) as primary_labeler,
    MIN(CASE WHEN il.labeler_mode = 'production' THEN il.fog_score END) as primary_fog_score,
    MIN(CASE WHEN il.labeler_mode = 'production' THEN il.fog_level END) as primary_fog_level,
    MIN(CASE WHEN il.labeler_mode = 'production' THEN il.confidence END) as primary_confidence,
    
    -- Shadow labeler comparison
    STRING_AGG(
        CASE WHEN il.labeler_mode = 'shadow' 
        THEN il.labeler_name || ':' || COALESCE(il.fog_score::text, 'null') 
        END, ',' ORDER BY il.labeler_name
    ) as shadow_labelers_scores,
    
    STRING_AGG(
        CASE WHEN il.labeler_mode = 'shadow' 
        THEN il.labeler_name || ':' || COALESCE(il.fog_level, 'null') 
        END, ',' ORDER BY il.labeler_name
    ) as shadow_labelers_levels,
    
    -- Agreement metrics
    COUNT(DISTINCT il.fog_level) as unique_fog_levels,
    MAX(il.fog_score) - MIN(il.fog_score) as fog_score_range,
    STDDEV(il.fog_score) as fog_score_disagreement,
    
    -- Execution performance comparison
    COUNT(*) as total_labelers_run,
    AVG(il.execution_time_ms) as avg_execution_time_ms,
    MAX(il.execution_time_ms) - MIN(il.execution_time_ms) as execution_time_range
    
FROM image_collections ic
JOIN image_labels il ON ic.id = il.image_id
WHERE ic.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ic.id, ic.webcam_id, ic.timestamp
HAVING COUNT(*) > 1  -- Only include images with multiple labelers
ORDER BY ic.timestamp DESC;

-- 4. Webcam-Specific Performance View
CREATE OR REPLACE VIEW webcam_labeler_performance AS
SELECT 
    w.id as webcam_id,
    w.name as webcam_name,
    il.labeler_name,
    il.labeler_mode,
    
    COUNT(*) as total_labels,
    AVG(il.execution_time_ms) as avg_execution_time_ms,
    AVG(il.confidence) as avg_confidence,
    AVG(il.fog_score) as avg_fog_score,
    
    -- Fog distribution for this webcam
    ROUND(100.0 * COUNT(CASE WHEN il.fog_level = 'Clear' THEN 1 END) / COUNT(*), 1) as clear_percentage,
    ROUND(100.0 * COUNT(CASE WHEN il.fog_level IN ('Light Fog', 'Moderate Fog', 'Heavy Fog', 'Very Heavy Fog') THEN 1 END) / COUNT(*), 1) as fog_percentage,
    
    MIN(il.created_at) as first_label,
    MAX(il.created_at) as last_label
    
FROM webcams w
JOIN image_collections ic ON w.id = ic.webcam_id
JOIN image_labels il ON ic.id = il.image_id
WHERE w.active = true
AND il.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY w.id, w.name, il.labeler_name, il.labeler_mode
ORDER BY w.name, il.labeler_name;

-- 5. Cost Analysis View
CREATE OR REPLACE VIEW labeler_cost_analysis AS
SELECT 
    il.labeler_name,
    il.labeler_mode,
    
    -- Daily costs
    DATE(il.created_at) as cost_date,
    COUNT(*) as daily_executions,
    SUM(il.api_cost_cents) as daily_cost_cents,
    AVG(il.api_cost_cents) as avg_cost_per_execution_cents,
    
    -- Cost efficiency (cost per confidence unit)
    AVG(il.api_cost_cents / NULLIF(il.confidence, 0)) as cost_per_confidence_unit,
    
    -- Running totals
    SUM(SUM(il.api_cost_cents)) OVER (
        PARTITION BY il.labeler_name, il.labeler_mode 
        ORDER BY DATE(il.created_at) 
        ROWS UNBOUNDED PRECEDING
    ) as cumulative_cost_cents
    
FROM image_labels il
WHERE il.api_cost_cents IS NOT NULL
AND il.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY il.labeler_name, il.labeler_mode, DATE(il.created_at)
ORDER BY cost_date DESC, il.labeler_name;

-- 6. Error Rate Analysis View
CREATE OR REPLACE VIEW labeler_reliability_analysis AS
SELECT 
    cr.id as collection_run_id,
    cr.timestamp as run_timestamp,
    cr.total_images,
    cr.successful_images,
    
    -- Labeler execution counts
    COUNT(DISTINCT il.labeler_name) as unique_labelers_attempted,
    COUNT(*) as total_labels_created,
    
    -- Expected vs actual labels
    cr.successful_images * (SELECT COUNT(*) FROM labeler_config WHERE enabled = true) as expected_labels,
    COUNT(*) as actual_labels,
    
    -- Success rates
    ROUND(100.0 * COUNT(*) / NULLIF(cr.successful_images * (SELECT COUNT(*) FROM labeler_config WHERE enabled = true), 0), 2) as labeling_success_rate,
    
    -- Performance summary
    AVG(il.execution_time_ms) as avg_execution_time_ms,
    MAX(il.execution_time_ms) as max_execution_time_ms,
    SUM(il.api_cost_cents) as total_run_cost_cents
    
FROM collection_runs cr
LEFT JOIN image_collections ic ON cr.id = ic.collection_run_id
LEFT JOIN image_labels il ON ic.id = il.image_id
WHERE cr.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY cr.id, cr.timestamp, cr.total_images, cr.successful_images
ORDER BY cr.timestamp DESC;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_image_labels_created_at_labeler ON image_labels(created_at, labeler_name);
CREATE INDEX IF NOT EXISTS idx_image_labels_mode_created_at ON image_labels(labeler_mode, created_at);
CREATE INDEX IF NOT EXISTS idx_image_collections_timestamp ON image_collections(timestamp);