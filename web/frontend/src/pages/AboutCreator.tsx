import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import AboutCreator from '../components/AboutCreator';

const AboutCreatorPage: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

      <main className="flex-1 container mx-auto px-6 py-8 mt-8">
        <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg">
          <AboutCreator />
        </div>
      </main>

      <footer className="bg-white/10 backdrop-blur-md border-t border-white/20 text-white py-6">
        <div className="container mx-auto px-6 text-center">
          <p className="text-blue-100">
            🌫️ KarlCam - Real-time fog tracking for San Francisco
          </p>
        </div>
      </footer>
    </div>
  );
};

export default AboutCreatorPage;