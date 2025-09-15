import React, { useState, useEffect } from 'react';
import { LabelerPerformance, LabelerComparison, DailyPerformance } from './types/labeler';
import { labelerApi } from './services/labelerApi';
import './PerformanceMonitor.css';

interface PerformanceMonitorProps {
  onNavigateBack: () => void;
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ onNavigateBack }) => {
  const [performanceData, setPerformanceData] = useState<LabelerPerformance[]>([]);
  const [comparisonData, setComparisonData] = useState<LabelerComparison[]>([]);
  const [dailyData, setDailyData] = useState<DailyPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'comparison' | 'trends'>('overview');
  const [selectedDays, setSelectedDays] = useState(7);

  useEffect(() => {
    loadData();
  }, [selectedDays]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [performance, comparison, daily] = await Promise.all([
        labelerApi.getPerformanceSummary(),
        labelerApi.getLabelerComparison(selectedDays),
        labelerApi.getDailyPerformance(selectedDays)
      ]);
      
      setPerformanceData(performance);
      setComparisonData(comparison);
      setDailyData(daily);
    } catch (err) {
      setError('Failed to load performance data');
      console.error('Failed to load performance data:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotalMetrics = () => {
    return performanceData.reduce(
      (acc, curr) => ({
        totalExecutions: acc.totalExecutions + curr.total_executions,
        totalCost: acc.totalCost + (curr.total_cost_cents || 0),
        avgConfidence: acc.avgConfidence + (curr.avg_confidence || 0),
        count: acc.count + 1
      }),
      { totalExecutions: 0, totalCost: 0, avgConfidence: 0, count: 0 }
    );
  };

  const getAgreementRate = () => {
    if (comparisonData.length === 0) return 0;
    const agreements = comparisonData.filter(
      c => c.fog_score_disagreement !== null && c.fog_score_disagreement < 10
    ).length;
    return Math.round((agreements / comparisonData.length) * 100);
  };

  if (loading) {
    return (
      <div className="performance-monitor">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading performance analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="performance-monitor">
        <div className="error-container">
          <h3>Error Loading Performance Data</h3>
          <p>{error}</p>
          <button onClick={loadData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const totalMetrics = calculateTotalMetrics();
  const agreementRate = getAgreementRate();

  return (
    <div className="performance-monitor">
      <div className="header">
        <button onClick={onNavigateBack} className="back-button">
          ← Back to Labelers
        </button>
        <h2>Performance Analytics</h2>
        <div className="time-selector">
          <label>Time Range:</label>
          <select 
            value={selectedDays}
            onChange={(e) => setSelectedDays(Number(e.target.value))}
          >
            <option value={1}>Last 24 hours</option>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        </div>
      </div>

      <div className="metrics-overview">
        <div className="metric-card">
          <h4>Total Executions</h4>
          <span className="metric-value">{totalMetrics.totalExecutions.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <h4>Total Cost</h4>
          <span className="metric-value">{labelerApi.formatCost(totalMetrics.totalCost)}</span>
        </div>
        <div className="metric-card">
          <h4>Avg Confidence</h4>
          <span className="metric-value">
            {totalMetrics.count > 0 
              ? labelerApi.formatConfidence(totalMetrics.avgConfidence / totalMetrics.count)
              : 'N/A'
            }
          </span>
        </div>
        <div className="metric-card">
          <h4>Agreement Rate</h4>
          <span className="metric-value">{agreementRate}%</span>
        </div>
      </div>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`tab ${activeTab === 'comparison' ? 'active' : ''}`}
          onClick={() => setActiveTab('comparison')}
        >
          ⚖️ Comparison
        </button>
        <button 
          className={`tab ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          📈 Trends
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <h3>Labeler Performance Summary</h3>
            <div className="performance-table">
              <table>
                <thead>
                  <tr>
                    <th>Labeler</th>
                    <th>Mode</th>
                    <th>Executions</th>
                    <th>Avg Time</th>
                    <th>Avg Confidence</th>
                    <th>Total Cost</th>
                    <th>Last 24h</th>
                  </tr>
                </thead>
                <tbody>
                  {performanceData.map((perf) => (
                    <tr key={perf.labeler_name}>
                      <td className="labeler-name">{perf.labeler_name}</td>
                      <td>
                        <span className={`mode-badge ${perf.labeler_mode}`}>
                          {perf.labeler_mode}
                        </span>
                      </td>
                      <td>{perf.total_executions.toLocaleString()}</td>
                      <td>{labelerApi.formatExecutionTime(perf.avg_execution_time_ms)}</td>
                      <td>{labelerApi.formatConfidence(perf.avg_confidence)}</td>
                      <td>{labelerApi.formatCost(perf.total_cost_cents)}</td>
                      <td>{perf.executions_last_24h}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'comparison' && (
          <div className="comparison-tab">
            <h3>Labeler Agreement Analysis</h3>
            <p className="tab-description">
              Images where multiple labelers produced different results. 
              Lower disagreement scores indicate better consensus.
            </p>
            <div className="comparison-table">
              <table>
                <thead>
                  <tr>
                    <th>Image ID</th>
                    <th>Webcam</th>
                    <th>Timestamp</th>
                    <th>Primary Result</th>
                    <th>Labelers Run</th>
                    <th>Disagreement</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.slice(0, 20).map((comp) => (
                    <tr key={comp.image_id}>
                      <td>{comp.image_id}</td>
                      <td>{comp.webcam_id}</td>
                      <td>{new Date(comp.image_timestamp).toLocaleString()}</td>
                      <td>
                        {comp.primary_fog_level && (
                          <span className={`fog-level ${comp.primary_fog_level.toLowerCase().replace(' ', '-')}`}>
                            {comp.primary_fog_level}
                          </span>
                        )}
                        {comp.primary_fog_score && (
                          <span className="fog-score">
                            ({comp.primary_fog_score.toFixed(1)})
                          </span>
                        )}
                      </td>
                      <td>{comp.total_labelers_run}</td>
                      <td>
                        {comp.fog_score_disagreement ? (
                          <span className={`disagreement ${comp.fog_score_disagreement > 20 ? 'high' : comp.fog_score_disagreement > 10 ? 'medium' : 'low'}`}>
                            {comp.fog_score_disagreement.toFixed(1)}
                          </span>
                        ) : (
                          'N/A'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="trends-tab">
            <h3>Daily Performance Trends</h3>
            <p className="tab-description">
              Daily execution patterns and performance metrics over time.
            </p>
            <div className="trends-summary">
              {dailyData.length > 0 ? (
                <div className="daily-grid">
                  {Array.from(new Set(dailyData.map(d => d.date)))
                    .sort((a, b) => b.localeCompare(a))
                    .slice(0, 7)
                    .map((date) => {
                      const dayData = dailyData.filter(d => d.date === date);
                      const totalExecutions = dayData.reduce((sum, d) => sum + d.daily_executions, 0);
                      const avgTime = dayData.reduce((sum, d) => sum + (d.avg_execution_time_ms || 0), 0) / dayData.length;
                      const totalCost = dayData.reduce((sum, d) => sum + (d.total_daily_cost_cents || 0), 0);
                      
                      return (
                        <div key={date} className="day-card">
                          <h4>{new Date(date).toLocaleDateString()}</h4>
                          <div className="day-stats">
                            <div className="day-stat">
                              <span className="stat-label">Executions:</span>
                              <span className="stat-value">{totalExecutions}</span>
                            </div>
                            <div className="day-stat">
                              <span className="stat-label">Avg Time:</span>
                              <span className="stat-value">{labelerApi.formatExecutionTime(avgTime)}</span>
                            </div>
                            <div className="day-stat">
                              <span className="stat-label">Cost:</span>
                              <span className="stat-value">{labelerApi.formatCost(totalCost)}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              ) : (
                <div className="no-data">
                  <p>No daily performance data available for the selected time range.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceMonitor;