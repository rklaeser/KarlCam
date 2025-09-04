import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();

  const getMenuItemClass = (path: string) => {
    return location.pathname === path
      ? "block text-blue-600 font-medium py-2 px-4 rounded-lg bg-blue-50"
      : "block text-gray-800 hover:text-blue-600 font-medium py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors";
  };

  const getMenuItemText = (path: string, text: string) => {
    return location.pathname === path ? text : text;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0" style={{ zIndex: 10000 }}>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      ></div>
      
      {/* Sidebar Panel */}
      <div className="absolute top-0 right-0 h-full w-80 bg-white/95 backdrop-blur-md shadow-2xl">
        <div className="p-6 h-full flex flex-col">
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Top Section */}
          <div>
            {/* Title */}
            <div className="mb-8 mt-4">
              <Link to="/">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent hover:from-blue-700 hover:to-purple-700 transition-all duration-300 cursor-pointer">
                  karl cam
                </h1>
                <p className="text-gray-600 mt-2 hover:text-gray-800 transition-colors cursor-pointer">Live San Francisco fog</p>
              </Link>
            </div>

            {/* View Toggle */}
            <div className="mb-6">
              <div className="flex bg-gray-100 rounded-lg p-1">
                <Link
                  to="/"
                  className={`flex-1 text-center py-2 px-4 rounded-md font-medium transition-all ${
                    location.pathname === '/' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Map
                </Link>
                <Link
                  to="/table"
                  className={`flex-1 text-center py-2 px-4 rounded-md font-medium transition-all ${
                    location.pathname === '/table' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Table
                </Link>
              </div>
            </div>

            {/* Main Links */}
            <nav className="space-y-4">
              <Link
                to="/measuring-fog"
                className={getMenuItemClass('/measuring-fog')}
              >
                {getMenuItemText('/measuring-fog', 'Measuring Fog with Cameras')}
              </Link>
              <Link
                to="/why-karlcam"
                className={getMenuItemClass('/why-karlcam')}
              >
                {getMenuItemText('/why-karlcam', 'Why KarlCam?')}
              </Link>
              <a
                href="https://x.com/KarlTheFog"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-gray-800 hover:text-blue-600 font-medium py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors"
              >
                Who is Karl the Fog? ↗
              </a>
            </nav>
          </div>

          {/* Spacer */}
          <div className="flex-1"></div>

          {/* Bottom Section - About Creator */}
          <div className="border-t border-gray-200 pt-4 mt-4 space-y-2">
            <Link
              to="/about"
              className="block text-gray-600 hover:text-blue-600 text-sm py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors"
            >
              How I built this
            </Link>
            <Link
              to="/about-creator"
              className="block text-gray-600 hover:text-blue-600 text-sm py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Made by Reed Klaeser
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;