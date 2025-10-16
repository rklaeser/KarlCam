import React, { useState } from 'react';
import FogMap from '../components/FogMap';
import Sidebar from '../components/Sidebar';
import MaintenanceBanner from '../components/MaintenanceBanner';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { useAppData, useAppActions } from '../context';
import { API_BASE_URL } from '../services/api';

const Home: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Get data and actions from context
  const { 
    cameras, 
    webcams,
    errors, 
    isNightMode
  } = useAppData();
  
  const { refreshData } = useAppActions();

  // Use the global error or specific errors for display
  const error = errors.global || errors.webcams || errors.systemStatus;

  return (
    <div className="h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col overflow-hidden">
      {/* Maintenance Banner */}
      <MaintenanceBanner isVisible={true} />
      
      {/* Hamburger Menu Button */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="fixed top-6 right-6 bg-white/90 backdrop-blur-sm text-gray-800 p-3 rounded-full shadow-lg hover:bg-white hover:shadow-xl transition-all duration-300"
        style={{ zIndex: 9999 }}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      {/* Full-width Map - takes full viewport */}
      <div className="flex-1 relative">
        <FogMap 
          webcams={webcams}
          cameras={cameras}
          apiBase={API_BASE_URL}
        />
        
        
        {/* Error overlay */}
        {error && webcams.length === 0 && (
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center" style={{ zIndex: 1000 }}>
            <div className="max-w-md mx-4">
              <ErrorDisplay
                error={error}
                onRetry={refreshData}
                variant="overlay"
                className="bg-white/95 backdrop-blur-sm border-white/20"
              />
            </div>
          </div>
        )}

        {/* Night mode overlay - shown when system status indicates night mode */}
        {!error && isNightMode && (
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900 to-blue-900 flex items-center justify-center" style={{ zIndex: 1000 }}>
            <div className="text-center text-white max-w-md mx-auto px-6">
              <div className="text-6xl mb-6">🌙</div>
              <h2 className="text-3xl font-bold mb-4">KarlCam is Sleeping</h2>
              <p className="text-blue-100 mb-6 leading-relaxed">
                Fog tracking is currently offline. We collect images and analyze conditions daily from 9 AM to 5 PM PT.
              </p>
              <p className="text-sm text-blue-200 mb-8">
                Check back tomorrow at 9 AM for fresh fog data!
              </p>
              <button 
                onClick={refreshData} 
                className="bg-white/20 backdrop-blur-sm text-white border border-white/30 px-6 py-3 rounded-lg font-semibold hover:bg-white/30 transition-all duration-300"
              >
                Check Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;