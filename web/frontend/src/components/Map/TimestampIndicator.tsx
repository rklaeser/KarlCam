import React from 'react';
import { getGlobalTimestamp, getRelativeTime } from '../../utils/timeUtils';

interface TimestampIndicatorProps {
  imageTimestamps: Map<string, Date>;
}

const TimestampIndicator: React.FC<TimestampIndicatorProps> = ({ imageTimestamps }) => {
  const { timestamp, color, allSame } = getGlobalTimestamp(imageTimestamps);
  
  if (!timestamp) return null;
  
  return (
    <div 
      className="absolute top-6 left-1/2 transform -translate-x-1/2 bg-white/95 backdrop-blur-sm rounded-full shadow-lg px-4 py-2 border border-gray-200 flex items-center gap-2 text-sm font-medium"
      style={{ zIndex: 1000 }}
    >
      <div 
        className="w-3 h-3 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
      ></div>
      <span className="text-gray-700">
        {allSame ? 'Updated' : 'Latest'} {getRelativeTime(timestamp)}
      </span>
    </div>
  );
};

export default TimestampIndicator;