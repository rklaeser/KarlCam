import React from 'react';
import { Link } from 'react-router-dom';

const FogLegend: React.FC = () => {
  return (
    <div 
      className="absolute bottom-6 left-6 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-4 border border-gray-200"
      style={{ zIndex: 1000 }}
    >
      <h4 className="font-semibold text-gray-800 mb-3 flex items-center text-sm">
        Visibility
        <Link 
          to="/measuring-fog"
          className="ml-2 w-4 h-4 bg-blue-100 text-blue-600 rounded-full text-xs font-bold hover:bg-blue-200 transition-colors inline-flex items-center justify-center"
          title="View fog intensity examples"
        >
          ?
        </Link>
      </h4>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#6c757d' }}></div>
          <span className="text-xs">No Data</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#28a745' }}></div>
          <span className="text-xs">Clear (0-20)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#ffc107' }}></div>
          <span className="text-xs">Light Fog (20-40)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#fd7e14' }}></div>
          <span className="text-xs">Moderate Fog (40-60)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#dc3545' }}></div>
          <span className="text-xs">Heavy Fog (60-80)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#6f42c1' }}></div>
          <span className="text-xs">Very Heavy Fog (80+)</span>
        </div>
      </div>
    </div>
  );
};

export default FogLegend;