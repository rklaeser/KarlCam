import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';

const MeasuringFog: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fogLevels = [
    {
      level: 'Clear',
      range: '0-20',
      color: '#28a745',
      description: 'No fog visible, clear visibility',
      exampleImage: '/images/fog-clear.jpg'
    },
    {
      level: 'Light Fog',
      range: '20-40',
      color: '#ffc107',
      description: 'Slight haze, visibility slightly reduced',
      exampleImage: '/images/fog-light.jpg'
    },
    {
      level: 'Moderate Fog',
      range: '40-60',
      color: '#fd7e14',
      description: 'Noticeable fog, landmarks partially obscured',
      exampleImage: '/images/fog-moderate.jpg'
    },
    {
      level: 'Heavy Fog',
      range: '60-80',
      color: '#dc3545',
      description: 'Dense fog, visibility significantly reduced',
      exampleImage: '/images/fog-heavy.jpg'
    },
    {
      level: 'Very Heavy Fog',
      range: '80+',
      color: '#6f42c1',
      description: 'Extremely dense fog, minimal visibility',
      exampleImage: '/images/fog-very-heavy.jpg'
    }
  ];

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
        <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-6 md:p-10">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-6">Measuring Fog with Cameras</h1>
          
          <p className="text-gray-600 text-lg mb-8 leading-relaxed">
            Our AI analyzes webcam images to determine fog intensity on a scale of 0-100. 
            The system evaluates visual features including visibility, contrast, and atmospheric conditions
            to provide real-time fog measurements across San Francisco.
          </p>

          <h2 className="text-2xl font-semibold text-gray-800 mb-6">Fog Intensity Levels</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {fogLevels.map((level) => (
              <div key={level.level} className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                <div className="p-4 bg-gray-50">
                  <div className="flex items-center gap-3 mb-2">
                    <div 
                      className="px-3 py-1 rounded-full text-white text-sm font-semibold"
                      style={{ backgroundColor: level.color }}
                    >
                      {level.range}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">{level.level}</h3>
                  </div>
                </div>
                
                <div className="p-4">
                  <div className="aspect-video bg-gray-100 rounded-lg border-2 border-dashed flex flex-col items-center justify-center mb-4" style={{ borderColor: level.color }}>
                    <div className="text-4xl mb-2">🌫️</div>
                    <div className="text-center">
                      <div className="text-sm font-medium text-gray-600">Example Image</div>
                      <div className="text-xs text-gray-500">{level.level}</div>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 leading-relaxed">{level.description}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">How It Works</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>AI models analyze webcam images every few minutes</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Visual features like contrast, edges, and color saturation are evaluated</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Each camera location receives a fog score from 0 (clear) to 100 (very heavy fog)</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Scores are displayed on the map with color-coded circles</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-6">
            <p className="text-sm text-gray-700 leading-relaxed">
              <strong>Note:</strong> Fog scores are estimates based on visual analysis. 
              Weather conditions, camera quality, and time of day can affect accuracy. 
              Always use multiple sources when making weather-dependent decisions.
            </p>
          </div>
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

export default MeasuringFog;