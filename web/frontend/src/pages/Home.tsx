import React, { useState } from 'react';
import FogMap from '../components/FogMap';
import Sidebar from '../components/Sidebar';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { useAppData, useAppActions } from '../context';
import { API_BASE_URL } from '../services/api';

const Home: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Get data and actions from context
  const {
    cameras,
    webcams,
    errors
  } = useAppData();
  
  const { refreshData } = useAppActions();

  // Use the global error or specific errors for display
  const error = errors.global || errors.webcams || errors.systemStatus;

  return (
    <div className="h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col overflow-hidden">
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
      </div>
    </div>
  );
};

export default Home;