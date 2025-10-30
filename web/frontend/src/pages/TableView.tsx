import React, { useState } from 'react';
import CameraTable from '../components/CameraTable';
import Sidebar from '../components/Sidebar';
import { useAppData, useAppActions } from '../context';

const TableView: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Get data and actions from context
  const { 
    cameras, 
    loading, 
    errors,
    isInitialLoading 
  } = useAppData();
  
  const { refreshData } = useAppActions();

  // Use specific camera error or global error
  const error = errors.cameras || errors.global;
  const isLoading = loading.cameras || isInitialLoading;

  if (isLoading && cameras.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-6"></div>
            <h2 className="text-2xl font-bold mb-2">Loading Camera Data...</h2>
            <p className="text-blue-100">Loading camera conditions...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && cameras.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-white">
            <h2 className="text-2xl font-bold mb-4">Unable to Load Camera Data</h2>
            <p className="text-blue-100 mb-6">{error}</p>
            <button 
              onClick={refreshData} 
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col">
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

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-6 py-8">
        <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">Camera Conditions</h1>
          <CameraTable 
            cameras={cameras}
            loading={isLoading}
          />
        </div>
      </main>
    </div>
  );
};

export default TableView;