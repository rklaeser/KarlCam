// TypeScript interfaces for labeler management

export interface LabelerConfig {
  name: string;
  mode: 'production' | 'shadow' | 'experimental' | 'deprecated';
  enabled: boolean;
  version: string;
  config: Record<string, any>;
}

export interface LabelerUpdate {
  mode?: 'production' | 'shadow' | 'experimental' | 'deprecated';
  enabled?: boolean;
  version?: string;
  config?: Record<string, any>;
}

export interface LabelerPerformance {
  labeler_name: string;
  labeler_mode: string;
  total_executions: number;
  avg_execution_time_ms: number | null;
  avg_confidence: number | null;
  avg_fog_score: number | null;
  total_cost_cents: number | null;
  executions_last_24h: number;
}

export interface LabelerDetailedPerformance {
  labeler_name: string;
  labeler_mode: string;
  execution_metrics: {
    total_executions: number;
    avg_execution_time_ms: number | null;
    median_execution_time_ms: number | null;
    min_execution_time_ms: number | null;
    max_execution_time_ms: number | null;
    executions_last_24h: number;
  };
  quality_metrics: {
    avg_confidence: number | null;
    avg_fog_score: number | null;
  };
  cost_metrics: {
    total_cost_cents: number | null;
    avg_cost_cents: number | null;
  };
  fog_distribution: {
    clear: number;
    light_fog: number;
    moderate_fog: number;
    heavy_fog: number;
    very_heavy_fog: number;
  };
  time_range: {
    first_execution: string | null;
    last_execution: string | null;
  };
}

export interface LabelerComparison {
  image_id: number;
  webcam_id: string;
  image_timestamp: string;
  primary_labeler: string | null;
  primary_fog_score: number | null;
  primary_fog_level: string | null;
  fog_score_disagreement: number | null;
  total_labelers_run: number;
}

export interface DailyPerformance {
  date: string;
  labeler_name: string;
  labeler_mode: string;
  daily_executions: number;
  avg_execution_time_ms: number | null;
  avg_cost_cents: number | null;
  avg_confidence: number | null;
  total_daily_cost_cents: number | null;
}

export interface ModeChangeRequest {
  mode: 'production' | 'shadow' | 'experimental' | 'deprecated';
}

export type LabelerMode = 'production' | 'shadow' | 'experimental' | 'deprecated';

export const LABELER_MODE_COLORS: Record<LabelerMode, string> = {
  production: '#28a745',
  shadow: '#6c757d', 
  experimental: '#ffc107',
  deprecated: '#dc3545'
};

export const LABELER_MODE_DESCRIPTIONS: Record<LabelerMode, string> = {
  production: 'Active in production pipeline',
  shadow: 'Runs alongside production for comparison',
  experimental: 'Testing phase, manual execution only',
  deprecated: 'No longer used, pending removal'
};