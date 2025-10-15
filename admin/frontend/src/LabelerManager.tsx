import React, { useState, useEffect } from 'react';
import { LabelerConfig, LabelerPerformance } from './types/labeler';
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

  const getPerformanceForLabeler = (name: string): LabelerPerformance | null => {
    return performance.find(p => p.labeler_name === name) || null;
  };

  const getStatusIcon = (enabled: boolean): string => {
    return enabled ? '🟢' : '🔴';
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
        <h2>Labeler Configuration</h2>
        <div className="header-actions">
          <button 
            onClick={onNavigateToPerformance}
            className="performance-button"
          >
            📊 View Performance Analytics
          </button>
          <button 
            onClick={loadData}
            className="refresh-button"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="config-notice">
        <h3>🔧 Configuration Management</h3>
        <p>
          Labeler configuration is now managed through environment variables for better deployment control.
          To modify labeler settings, update environment variables and redeploy the service.
        </p>
        <div className="env-vars">
          <h4>Environment Variables:</h4>
          <ul>
            <li><code>GEMINI_LABELER_ENABLED</code> - Enable/disable Gemini labeler (default: true)</li>
            <li><code>GEMINI_MASKED_LABELER_ENABLED</code> - Enable/disable Gemini Masked labeler (default: false)</li>
            <li><code>GEMINI_MODEL</code> - Gemini model name (default: gemini-2.0-flash)</li>
            <li><code>GEMINI_TEMPERATURE</code> - Model temperature (default: 0.1)</li>
            <li><code>GEMINI_LABELER_VERSION</code> - Labeler version (default: 1.0)</li>
          </ul>
        </div>
      </div>

      <div className="summary-stats">
        <div className="stat-card">
          <h4>Total Labelers</h4>
          <span className="stat-value">{labelers.length}</span>
        </div>
        <div className="stat-card">
          <h4>Enabled</h4>
          <span className="stat-value enabled">
            {labelers.filter(l => l.enabled).length}
          </span>
        </div>
        <div className="stat-card">
          <h4>Disabled</h4>
          <span className="stat-value disabled">
            {labelers.filter(l => !l.enabled).length}
          </span>
        </div>
      </div>

      <div className="labeler-grid">
        {labelers.map((labeler) => {
          const perf = getPerformanceForLabeler(labeler.name);
          
          return (
            <div key={labeler.name} className={`labeler-card ${labeler.enabled ? 'enabled' : 'disabled'}`}>
              <div className="labeler-header">
                <div className="labeler-title">
                  <span className="status-icon">{getStatusIcon(labeler.enabled)}</span>
                  <h3>{labeler.name}</h3>
                  <span 
                    className={`status-badge ${labeler.enabled ? 'enabled' : 'disabled'}`}
                  >
                    {labeler.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>

              <div className="labeler-info">
                <div className="info-row">
                  <span className="label">Version:</span>
                  <span>{labeler.version}</span>
                </div>
                <div className="info-row">
                  <span className="label">Status:</span>
                  <span 
                    className={`status-text ${labeler.enabled ? 'enabled' : 'disabled'}`}
                  >
                    {labeler.enabled ? 'Active in pipeline' : 'Not running'}
                  </span>
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
          <p>Configure labelers using environment variables and restart the service.</p>
        </div>
      )}
    </div>
  );
};

export default LabelerManager;