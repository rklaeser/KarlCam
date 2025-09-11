import React from 'react';
import { CameraConditions } from '../types';

interface CameraTableProps {
  cameras: CameraConditions[];
  loading: boolean;
}

const CameraTable: React.FC<CameraTableProps> = ({ cameras, loading }) => {
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-300 rounded w-3/4"></div>
          <div className="h-4 bg-gray-300 rounded w-1/2"></div>
          <div className="h-4 bg-gray-300 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  const getFogEmoji = (fogLevel: string): string => {
    switch (fogLevel.toLowerCase()) {
      case 'clear': return '☀️';
      case 'light fog': return '🌤️';
      case 'moderate fog': return '🌫️';
      case 'heavy fog': return '🌁';
      case 'very heavy fog': return '🌁';
      default: return '❓';
    }
  };

  const getFogDescription = (fogScore: number): string => {
    const score = fogScore || 0;
    if (score < 20) {
      return 'Crystal clear visibility with blue skies';
    } else if (score < 40) {
      return 'Light haze or mist in the air';
    } else if (score < 60) {
      return 'Moderate fog reducing visibility';
    } else if (score < 80) {
      return 'Heavy fog with limited visibility';
    } else {
      return 'Very dense fog, visibility severely limited';
    }
  };

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'No data';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return '#28a745'; // Green
    if (confidence >= 60) return '#ffc107'; // Yellow
    return '#dc3545'; // Red
  };

  return (
    <div className="overflow-x-auto">
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full border-collapse">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-4 text-left font-semibold text-gray-700 text-sm border-b-2 border-gray-200">Camera</th>
              <th className="px-3 py-4 text-left font-semibold text-gray-700 text-sm border-b-2 border-gray-200">Conditions</th>
              <th className="px-3 py-4 text-left font-semibold text-gray-700 text-sm border-b-2 border-gray-200">Fog Score</th>
              <th className="px-3 py-4 text-left font-semibold text-gray-700 text-sm border-b-2 border-gray-200">AI Confidence</th>
              <th className="px-3 py-4 text-left font-semibold text-gray-700 text-sm border-b-2 border-gray-200">Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map((camera) => (
              <tr 
                key={camera.id} 
                className={`hover:bg-gray-50 transition-colors ${!camera.active ? 'opacity-60' : ''}`}
              >
                <td className="px-3 py-4 border-b border-gray-100 min-w-[150px]">
                  <div className="font-semibold text-gray-800 mb-1">
                    📹 {camera.name}
                  </div>
                  <div className="text-sm text-gray-600">
                    📍 {camera.lat?.toFixed(3) || '0.000'}, {camera.lon?.toFixed(3) || '0.000'}
                  </div>
                </td>
                
                <td className="px-3 py-4 border-b border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">
                      {getFogEmoji(camera.fog_level)}
                    </div>
                    <div className="flex flex-col">
                      <div className="font-semibold text-gray-800 mb-0.5">{camera.fog_level}</div>
                      <div className="text-xs text-gray-600 max-w-[200px]">
                        {getFogDescription(camera.fog_score)}
                      </div>
                    </div>
                  </div>
                </td>
                
                <td className="px-3 py-4 border-b border-gray-100 min-w-[100px]">
                  <div className="text-xl font-semibold text-gray-800 mb-1">
                    <span>{camera.fog_score?.toFixed(1) || '0.0'}</span>
                    <span className="text-sm font-normal text-gray-500">/100</span>
                  </div>
                  <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full transition-all duration-300 ease-in-out rounded-full"
                      style={{ 
                        width: `${camera.fog_score || 0}%`,
                        backgroundColor: (camera.fog_score || 0) > 50 ? '#dc2626' : '#16a34a'
                      }}
                    ></div>
                  </div>
                </td>
                
                <td className="px-3 py-4 border-b border-gray-100">
                  <span 
                    className="font-semibold text-lg"
                    style={{ color: getConfidenceColor(camera.confidence || 0) }}
                  >
                    {camera.confidence?.toFixed(1) || '0.0'}%
                  </span>
                </td>
                
                <td className="px-3 py-4 border-b border-gray-100 min-w-[120px] text-sm text-gray-600">
                  🕐 {formatTimestamp(camera.timestamp)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {cameras.length === 0 && (
        <div className="text-center py-10 text-gray-600">
          <p className="mb-2">No camera data available.</p>
          <p>Cameras will appear as data becomes available.</p>
        </div>
      )}
    </div>
  );
};

export default CameraTable;