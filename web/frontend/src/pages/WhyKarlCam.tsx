import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';

const WhyKarlCam: React.FC = () => {
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
        <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-6 md:p-10">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-6">Why KarlCam?</h1>
          
          <div className="prose prose-lg max-w-none text-gray-600 mb-8">
            <p className="leading-relaxed mb-4">
              I made KarlCam because I wanted to <a href="/about" className="text-blue-600 hover:text-blue-800 underline">learn</a> but also because I found myself cursing the fog and its fickleness and was seeking a better way to avoid it. Here's roughly how it went down:
            </p>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">User Story</h3>
              
              <div className="space-y-3 text-gray-700">
                <p><strong>As a</strong> San Francisco cyclist planning a bike ride,</p>
                <p><strong>I want</strong> to see real-time ground-level fog conditions across different neighborhoods,</p>
                <p><strong>So that</strong> I can choose a route with sun or avoid areas where fog is at ground level.</p>
              </div>
              
              <div className="mt-4 pt-4 border-t border-blue-200">
                <h4 className="font-semibold text-gray-800 mb-2">Acceptance Criteria:</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• Weather apps only provide neighborhood-level forecasts without ground-truth data</li>
                  <li>• <a href="https://fog.today/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline">fog.today</a> shows satellite view but not ground-level visibility</li>
                  <li>• Need hyperlocal visibility data across San Francisco's varied microclimates</li>
                  <li>• Must show current conditions, not just forecasts</li>
                </ul>
              </div>
            </div>
            
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Solution: Real-time SF fog visibility map using public webcam feeds</h3>
              
              <div className="mb-4">
                <h4 className="font-semibold text-gray-800 mb-2">How it works:</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• Aggregates 20-30 public webcams across SF neighborhoods</li>
                  <li>• Uses computer vision to detect ground-level fog density</li>
                  <li>• Displays color-coded fog conditions on interactive map</li>
                  <li>• Updates every 5-10 minutes</li>
                </ul>
              </div>
              
              <div className="mb-4">
                <h4 className="font-semibold text-gray-800 mb-2">Key features:</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• Live visibility status (not forecasts)</li>
                  <li>• Neighborhood-level detail for SF microclimates</li>
                  <li>• Route planning with fog avoidance</li>
                  <li>• Mobile-friendly for checking before/during rides</li>
                </ul>
              </div>
              
              <p className="text-sm text-gray-700">
                <strong>Delivers:</strong> Ground-truth fog data so cyclists can choose sunny routes and avoid foggy areas
              </p>
            </div>
            
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-800 mb-2">But wait... why do we need computer vision?</h4>
              <p className="text-gray-700 mb-3">
                If Reed can see the camera images, what is the value of the computer vision classification of fog density?
              </p>
              <p className="text-gray-700">
                The classification lets Reed scan the map to quickly understand where and how severe the fog is. 
                Scanning lots of cameras isn't very easy, but if that's all Reed needed then an existing webcam map like{' '}
                <a href="https://www.windy.com/-Webcams-San-Francisco-Marina-District/webcams/1693167474?37.807,-122.447,12" 
                   target="_blank" 
                   rel="noopener noreferrer" 
                   className="text-blue-600 hover:text-blue-800 underline">
                   Windy
                </a> would meet Reed's need more simply.
              </p>
            </div>
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

export default WhyKarlCam;