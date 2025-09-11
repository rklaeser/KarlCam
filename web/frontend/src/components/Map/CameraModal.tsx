import React, { useState, useEffect } from 'react';
import { getFogBadgeColor } from '../../utils/mapUtils';

interface Webcam {
  id: string;
  name: string;
  lat: number;
  lon: number;
  url: string;
  video_url?: string;
  description: string;
  active: boolean;
}

interface CameraConditions {
  id: string;
  name: string;
  lat: number;
  lon: number;
  fog_score: number;
  fog_level: string;
  confidence: number;
  active: boolean;
}

interface CameraModalProps {
  isOpen: boolean;
  webcam: Webcam | null;
  cameras: CameraConditions[];
  onClose: () => void;
  fetchImage: (webcamId: string) => Promise<string | null>;
  cachedImageUrl?: string | undefined;
}

const CameraModal: React.FC<CameraModalProps> = ({
  isOpen,
  webcam,
  cameras,
  onClose,
  fetchImage,
  cachedImageUrl
}) => {
  const [modalImageUrl, setModalImageUrl] = useState<string | null>(null);
  const [modalImageLoading, setModalImageLoading] = useState(false);

  useEffect(() => {
    if (isOpen && webcam) {
      setModalImageUrl(null);
      setModalImageLoading(true);
      
      // Use cached image if available, otherwise fetch
      if (cachedImageUrl) {
        setModalImageUrl(cachedImageUrl);
        setModalImageLoading(false);
      } else {
        fetchModalImage(webcam.id);
      }
    }
  }, [isOpen, webcam, cachedImageUrl]);

  const fetchModalImage = async (webcamId: string) => {
    try {
      const imageUrl = await fetchImage(webcamId);
      if (imageUrl) {
        setModalImageUrl(imageUrl);
      }
    } catch (error) {
      console.error(`Failed to fetch modal image:`, error);
    } finally {
      setModalImageLoading(false);
    }
  };

  if (!isOpen || !webcam) return null;

  const cameraData = cameras.find(cam => 
    cam.id === webcam.id || 
    (Math.abs(cam.lat - webcam.lat) < 0.001 && Math.abs(cam.lon - webcam.lon) < 0.001)
  );
  
  const fogScore = cameraData?.fog_score ?? 0;
  const fogLevel = cameraData?.fog_level ?? 'No data';
  const confidence = cameraData?.confidence ?? 0;

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 z-[2000] flex items-end">
        <div 
          className="fixed inset-0" 
          onClick={onClose}
        />
        <div 
          className="bg-white w-full h-3/4 rounded-t-2xl shadow-2xl transform transition-transform duration-300 ease-out relative z-10"
          style={{ animation: 'slideUp 0.3s ease-out' }}
        >
          {/* Header with Fog Conditions and Close button */}
          <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between">
            <div className="flex items-center gap-3 flex-wrap bg-white/90 backdrop-blur-sm rounded-full px-4 py-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getFogBadgeColor(fogLevel)}`}>
                {fogLevel}
              </span>
              <span className="text-sm text-gray-600">
                Score: <span className="font-medium text-gray-800">{fogScore.toFixed(1)}/100</span>
              </span>
              <span className="text-sm text-gray-600">
                Confidence: <span className="font-medium text-gray-800">{confidence.toFixed(1)}%</span>
              </span>
            </div>
            
            <button
              onClick={onClose}
              className="bg-black bg-opacity-20 hover:bg-opacity-40 text-white rounded-full w-8 h-8 flex items-center justify-center transition-all flex-shrink-0"
            >
              ✕
            </button>
          </div>
          
          {/* Handle bar */}
          <div className="flex justify-center pt-2">
            <div className="w-12 h-1 bg-gray-300 rounded-full"></div>
          </div>
          
          <div className="p-6 pt-16 h-full overflow-y-auto">
            {/* Image Section */}
            <div className="mb-6">
              {modalImageLoading ? (
                <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                  <div className="animate-pulse text-gray-500">📷 Loading image...</div>
                </div>
              ) : modalImageUrl ? (
                <img 
                  src={modalImageUrl}
                  alt={`${webcam.name} latest view`}
                  className="w-full max-w-3xl mx-auto object-contain rounded-lg shadow-lg bg-gray-50"
                  style={{ maxHeight: '60vh', minHeight: '200px' }}
                />
              ) : (
                <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center text-gray-500">
                  📷 No recent image available
                </div>
              )}
            </div>
            
            {/* Content Section */}
            <div className="flex flex-wrap items-start justify-between gap-4">
              <h2 className="text-2xl font-bold text-gray-800 flex-1 min-w-0">{webcam.name}</h2>
              {webcam.video_url && (
                <a 
                  href={webcam.video_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 shadow-lg flex-shrink-0"
                >
                  📹 Live video
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes slideUp {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }
      `}</style>
    </>
  );
};

export default CameraModal;