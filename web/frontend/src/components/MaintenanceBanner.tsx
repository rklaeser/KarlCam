import React from 'react';

interface MaintenanceBannerProps {
  isVisible: boolean;
}

const MaintenanceBanner: React.FC<MaintenanceBannerProps> = ({ isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="bg-amber-500 text-white p-4 text-center shadow-lg relative z-50">
      <div className="max-w-4xl mx-auto flex items-center justify-center space-x-3">
        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <div>
          <span className="font-semibold">Maintenance Notice:</span>
          <span className="ml-2">
            KarlCam data collection is temporarily paused while we train an improved fog detection model to reduce operational costs. 
            Current data shows the last collection from recent activity.
          </span>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceBanner;