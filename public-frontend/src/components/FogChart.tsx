import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface HistoryEntry {
  timestamp: string;
  sf_time: string;
  fog_score: number;
  fog_level: string;
}

interface FogChartProps {
  history: HistoryEntry[];
}

const FogChart: React.FC<FogChartProps> = ({ history }) => {
  if (history.length === 0) {
    return (
      <div className="fog-chart empty">
        <div className="empty-chart">
          <p>No historical data available</p>
        </div>
      </div>
    );
  }

  // Sort history by timestamp
  const sortedHistory = [...history].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Prepare chart data
  const labels = sortedHistory.map(entry => {
    const date = new Date(entry.sf_time || entry.timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  });

  const fogScores = sortedHistory.map(entry => entry.fog_score);

  // Create color gradient based on fog levels
  const backgroundColors = fogScores.map(score => {
    if (score < 20) return 'rgba(40, 167, 69, 0.2)';   // Green
    if (score < 40) return 'rgba(255, 193, 7, 0.2)';   // Yellow
    if (score < 60) return 'rgba(253, 126, 20, 0.2)';  // Orange
    if (score < 80) return 'rgba(220, 53, 69, 0.2)';   // Red
    return 'rgba(111, 66, 193, 0.2)';                  // Purple
  });

  const borderColors = fogScores.map(score => {
    if (score < 20) return 'rgba(40, 167, 69, 1)';
    if (score < 40) return 'rgba(255, 193, 7, 1)';
    if (score < 60) return 'rgba(253, 126, 20, 1)';
    if (score < 80) return 'rgba(220, 53, 69, 1)';
    return 'rgba(111, 66, 193, 1)';
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'Fog Score',
        data: fogScores,
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.1)',
        pointBackgroundColor: borderColors,
        pointBorderColor: borderColors,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.4,
        fill: true
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: false
      },
      tooltip: {
        callbacks: {
          title: (context: any) => {
            const index = context[0].dataIndex;
            const entry = sortedHistory[index];
            const date = new Date(entry.sf_time || entry.timestamp);
            return date.toLocaleString();
          },
          label: (context: any) => {
            const index = context.dataIndex;
            const entry = sortedHistory[index];
            return [
              `Fog Score: ${context.parsed.y.toFixed(1)}/100`,
              `Level: ${entry.fog_level}`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time (PST)'
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      y: {
        min: 0,
        max: 100,
        title: {
          display: true,
          text: 'Fog Score'
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          callback: function(value: any) {
            return value + '/100';
          }
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index' as const
    }
  };

  // Calculate some statistics
  const avgFogScore = fogScores.reduce((a, b) => a + b, 0) / fogScores.length;
  const maxFogScore = Math.max(...fogScores);
  const minFogScore = Math.min(...fogScores);

  return (
    <div className="fog-chart">
      <div className="chart-container">
        <Line data={data} options={options} height={300} />
      </div>
      
      <div className="chart-stats">
        <div className="stat">
          <span className="stat-label">Average:</span>
          <span className="stat-value">{avgFogScore.toFixed(1)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Peak:</span>
          <span className="stat-value">{maxFogScore.toFixed(1)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Lowest:</span>
          <span className="stat-value">{minFogScore.toFixed(1)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Data Points:</span>
          <span className="stat-value">{history.length}</span>
        </div>
      </div>
    </div>
  );
};

export default FogChart;