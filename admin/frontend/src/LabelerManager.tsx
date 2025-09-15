import React, { useState, useEffect } from 'react';
import { LabelerConfig, LabelerPerformance, LabelerMode, LABELER_MODE_COLORS, LABELER_MODE_DESCRIPTIONS } from './types/labeler';
import { labelerApi } from './services/labelerApi';
import './LabelerManager.css';

interface LabelerManagerProps {
  onNavigateToPerformance: () => void;
}

const LabelerManager: React.FC<LabelerManagerProps> = ({ onNavigateToPerformance }) => {
  const [labelers, setLabelers] = useState<LabelerConfig[]>([]);
  const [performance, setPerformance] = useState<LabelerPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLabeler, setSelectedLabeler] = useState<LabelerConfig | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [labelersData, performanceData] = await Promise.all([
        labelerApi.getAllLabelers(),
        labelerApi.getPerformanceSummary()
      ]);
      
      setLabelers(labelersData);
      setPerformance(performanceData);
    } catch (err) {
      setError('Failed to load labeler data. Make sure the admin backend is running.');
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEnabled = async (name: string, currentEnabled: boolean) => {
    try {
      setActionLoading(name);
      
      if (currentEnabled) {
        await labelerApi.disableLabeler(name);
      } else {
        await labelerApi.enableLabeler(name);
      }
      
      await loadData();
    } catch (err) {
      setError(`Failed to ${currentEnabled ? 'disable' : 'enable'} labeler`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleModeChange = async (name: string, newMode: LabelerMode) => {
    try {
      setActionLoading(name);
      await labelerApi.setLabelerMode(name, newMode);
      await loadData();
    } catch (err) {
      setError(`Failed to change labeler mode`);
    } finally {
      setActionLoading(null);
    }
  };

  const getPerformanceForLabeler = (name: string): LabelerPerformance | null => {
    return performance.find(p => p.labeler_name === name) || null;
  };

  const getModeIcon = (mode: LabelerMode): string => {
    switch (mode) {
      case 'production': return '🟢';
      case 'shadow': return '👥';
      case 'experimental': return '🧪';
      case 'deprecated': return '🔴';
      default: return '❓';
    }
  };

  if (loading) {
    return (
      <div className="labeler-manager">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading labeler configurations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="labeler-manager">
        <div className="error-container">
          <h3>Error Loading Data</h3>
          <p>{error}</p>
          <button onClick={loadData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="labeler-manager">
      <div className="header">
        <h2>Labeler Management</h2>
        <div className="header-actions">
          <button 
            onClick={onNavigateToPerformance}
            className="performance-button"
          >
            📊 View Performance Analytics
          </button>
          <button 
            onClick={() => setShowCreateForm(true)}
            className="create-button"
          >
            ➕ Create New Labeler
          </button>
          <button 
            onClick={loadData}
            className="refresh-button"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="summary-stats">
        <div className="stat-card">
          <h4>Total Labelers</h4>
          <span className="stat-value">{labelers.length}</span>
        </div>
        <div className="stat-card">
          <h4>Production</h4>
          <span className="stat-value production">
            {labelers.filter(l => l.mode === 'production' && l.enabled).length}
          </span>
        </div>
        <div className="stat-card">
          <h4>Shadow</h4>
          <span className="stat-value shadow">
            {labelers.filter(l => l.mode === 'shadow' && l.enabled).length}
          </span>
        </div>
        <div className="stat-card">
          <h4>Experimental</h4>
          <span className="stat-value experimental">
            {labelers.filter(l => l.mode === 'experimental' && l.enabled).length}
          </span>
        </div>
      </div>

      <div className="labeler-grid">
        {labelers.map((labeler) => {
          const perf = getPerformanceForLabeler(labeler.name);
          const isLoading = actionLoading === labeler.name;
          
          return (
            <div key={labeler.name} className={`labeler-card ${labeler.mode}`}>
              <div className="labeler-header">
                <div className="labeler-title">
                  <span className="mode-icon">{getModeIcon(labeler.mode)}</span>
                  <h3>{labeler.name}</h3>
                  <span 
                    className={`status-badge ${labeler.enabled ? 'enabled' : 'disabled'}`}
                  >
                    {labeler.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="labeler-actions">
                  <button
                    onClick={() => handleToggleEnabled(labeler.name, labeler.enabled)}
                    disabled={isLoading}
                    className={`toggle-button ${labeler.enabled ? 'disable' : 'enable'}`}
                  >
                    {isLoading ? '⏳' : labeler.enabled ? '⏸️' : '▶️'}
                  </button>
                </div>
              </div>

              <div className="labeler-info">
                <div className="info-row">
                  <span className="label">Mode:</span>
                  <span 
                    className="mode-badge"
                    style={{ backgroundColor: LABELER_MODE_COLORS[labeler.mode] }}
                  >
                    {labeler.mode}
                  </span>
                </div>
                <div className="info-row">
                  <span className="label">Version:</span>
                  <span>{labeler.version}</span>
                </div>
                <div className="mode-description">
                  {LABELER_MODE_DESCRIPTIONS[labeler.mode]}
                </div>
              </div>

              {perf && (
                <div className="performance-preview">
                  <h4>Recent Performance</h4>
                  <div className="perf-stats">
                    <div className="perf-stat">
                      <span className="perf-label">Executions:</span>
                      <span className="perf-value">{perf.total_executions}</span>
                    </div>
                    <div className="perf-stat">
                      <span className="perf-label">Avg Time:</span>
                      <span className="perf-value">
                        {labelerApi.formatExecutionTime(perf.avg_execution_time_ms)}
                      </span>
                    </div>
                    <div className="perf-stat">
                      <span className="perf-label">Avg Confidence:</span>
                      <span className="perf-value">
                        {labelerApi.formatConfidence(perf.avg_confidence)}
                      </span>
                    </div>
                    <div className="perf-stat">
                      <span className="perf-label">Total Cost:</span>
                      <span className="perf-value">
                        {labelerApi.formatCost(perf.total_cost_cents)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="mode-controls">
                <label>Change Mode:</label>
                <select
                  value={labeler.mode}
                  onChange={(e) => handleModeChange(labeler.name, e.target.value as LabelerMode)}
                  disabled={isLoading}
                  className="mode-select"
                >
                  <option value="experimental">🧪 Experimental</option>
                  <option value="shadow">👥 Shadow</option>
                  <option value="production">🟢 Production</option>
                  <option value="deprecated">🔴 Deprecated</option>
                </select>
              </div>

              {labeler.config && Object.keys(labeler.config).length > 0 && (
                <div className="config-preview">
                  <h4>Configuration</h4>
                  <pre className="config-json">
                    {JSON.stringify(labeler.config, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {labelers.length === 0 && (
        <div className="empty-state">
          <h3>No Labelers Configured</h3>
          <p>Create your first labeler to get started with experimental labeling.</p>
          <button onClick={() => setShowCreateForm(true)} className="create-button">
            ➕ Create First Labeler
          </button>
        </div>
      )}
    </div>
  );
};

export default LabelerManager;