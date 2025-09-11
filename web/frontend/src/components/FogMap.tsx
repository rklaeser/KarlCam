import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import { Link } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

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

interface FogMapProps {
  webcams: Webcam[];
  cameras?: CameraConditions[];
  apiBase: string;
}

const FogMap: React.FC<FogMapProps> = ({ webcams, cameras = [], apiBase }) => {
  // State for managing marker images
  const [markerImages, setMarkerImages] = useState<Map<string, string>>(new Map());
  const [loadingImages, setLoadingImages] = useState<Set<string>>(new Set());
  const [imageTimestamps, setImageTimestamps] = useState<Map<string, Date>>(new Map());
  
  // Modal state
  const [selectedWebcam, setSelectedWebcam] = useState<Webcam | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalImageUrl, setModalImageUrl] = useState<string | null>(null);
  const [modalImageLoading, setModalImageLoading] = useState(false);

  // Load marker images progressively as they become available
  useEffect(() => {
    if (webcams.length === 0) return;

    console.log('🚀 Loading images for', webcams.length, 'webcams');
    
    const abortController = new AbortController();
    
    const loadImage = async (webcam: Webcam) => {
      try {
        const response = await fetch(
          `${apiBase}/api/public/cameras/${webcam.id}/latest-image`,
          { signal: abortController.signal }
        );
        const data = await response.json();
        
        if (response.ok && data.image_url) {
          console.log(`✅ Loaded image for ${webcam.id}`, data);
          
          // Update state immediately for this specific image
          setMarkerImages(prev => new Map(prev.set(webcam.id, data.image_url)));
          
          // Store timestamp if available
          if (data.timestamp) {
            const timestamp = new Date(data.timestamp);
            setImageTimestamps(prev => new Map(prev.set(webcam.id, timestamp)));
          }
          
          setLoadingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(webcam.id);
            return newSet;
          });
        } else {
          console.warn(`⚠️ No image for ${webcam.id}`);
          setLoadingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(webcam.id);
            return newSet;
          });
        }
      } catch (error: unknown) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.error(`❌ Failed to load image for ${webcam.id}:`, error);
        }
        setLoadingImages(prev => {
          const newSet = new Set(prev);
          newSet.delete(webcam.id);
          return newSet;
        });
      }
    };
    
    // Clear previous images and set loading state
    setMarkerImages(new Map());
    setImageTimestamps(new Map());
    setLoadingImages(new Set(webcams.map(w => w.id)));
    
    // Start loading all images independently
    webcams.forEach(webcam => loadImage(webcam));
    
    // Cleanup function
    return () => {
      abortController.abort();
    };
  }, [webcams, apiBase]);

  const handleMarkerClick = (webcam: Webcam) => {
    setSelectedWebcam(webcam);
    setIsModalOpen(true);
    setModalImageUrl(null);
    setModalImageLoading(true);
    
    // Use cached image if available, otherwise fetch
    const cachedImage = markerImages.get(webcam.id);
    if (cachedImage) {
      setModalImageUrl(cachedImage);
      setModalImageLoading(false);
    } else {
      fetchModalImage(webcam.id);
    }
  };

  const fetchModalImage = async (webcamId: string) => {
    try {
      const response = await fetch(`${apiBase}/api/public/cameras/${webcamId}/latest-image`);
      const data = await response.json();
      
      if (response.ok && data.image_url) {
        setModalImageUrl(data.image_url);
        // Also cache it for future use
        setMarkerImages(prev => new Map(prev.set(webcamId, data.image_url)));
        
        // Store timestamp if available
        if (data.timestamp) {
          const timestamp = new Date(data.timestamp);
          setImageTimestamps(prev => new Map(prev.set(webcamId, timestamp)));
        }
      }
    } catch (error) {
      console.error(`Failed to fetch modal image:`, error);
    } finally {
      setModalImageLoading(false);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedWebcam(null);
    setModalImageUrl(null);
  };

  // Utility function to format relative time
  const getRelativeTime = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    return date.toLocaleDateString();
  };

  // Get the most recent timestamp and determine if images are from same collection
  const getGlobalTimestamp = (): { timestamp: Date | null; color: string; allSame: boolean } => {
    const timestamps = Array.from(imageTimestamps.values());
    if (timestamps.length === 0) return { timestamp: null, color: '#6c757d', allSame: false };

    // Find most recent timestamp
    const mostRecent = new Date(Math.max(...timestamps.map(t => t.getTime())));
    
    // Check if all timestamps are within 10 minutes of each other (same collection run)
    const oldestInCollection = new Date(Math.min(...timestamps.map(t => t.getTime())));
    const diffMinutes = (mostRecent.getTime() - oldestInCollection.getTime()) / (1000 * 60);
    const allSame = diffMinutes <= 10;

    // Determine color based on age
    const ageMinutes = (new Date().getTime() - mostRecent.getTime()) / (1000 * 60);
    let color = '#28a745'; // Green - fresh (< 30 min)
    if (ageMinutes > 120) color = '#dc3545'; // Red - old (> 2 hours)
    else if (ageMinutes > 60) color = '#ffc107'; // Yellow - moderate (> 1 hour)

    return { timestamp: mostRecent, color, allSame };
  };

  const getFogColor = (fogScore: number, hasData: boolean = true): string => {
    if (!hasData) return '#6c757d'; // Grey - No data
    if (fogScore < 20) return '#28a745'; // Green - Clear
    if (fogScore < 40) return '#ffc107'; // Yellow - Light fog
    if (fogScore < 60) return '#fd7e14'; // Orange - Moderate fog
    if (fogScore < 80) return '#dc3545'; // Red - Heavy fog
    return '#6f42c1'; // Purple - Very heavy fog
  };

  const createMarkerIcon = (webcamId: string, fogScore: number, hasData: boolean = true): L.DivIcon => {
    const borderColor = getFogColor(fogScore, hasData);
    const size = 80;
    const imageUrl = markerImages.get(webcamId);
    const isLoading = loadingImages.has(webcamId);
    
    // Build the inner content based on state
    let innerContent: string;
    if (imageUrl) {
      innerContent = `<img src="${imageUrl}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;" alt="Camera view" />`;
    } else if (isLoading) {
      innerContent = '<div style="animation: pulse 2s infinite;">📷</div>';
    } else {
      innerContent = '📷';
    }
    
    const html = `
      <div style="
        width: ${size}px;
        height: ${size}px;
        border: 3px solid ${borderColor};
        border-radius: 50%;
        overflow: hidden;
        position: relative;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #666;
        font-size: 16px;
      ">
        ${innerContent}
      </div>
      <style>
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      </style>
    `;

    return L.divIcon({
      html: html,
      className: 'camera-marker',
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
      popupAnchor: [0, -(size/2) - 5]
    });
  };

  // San Francisco bounds
  const center: [number, number] = [37.7749, -122.4194];
  const bounds: [[number, number], [number, number]] = [
    [37.7, -122.5], // Southwest
    [37.8, -122.35]  // Northeast
  ];

  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={center}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
        bounds={bounds}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        
        {/* Render markers only when images are loaded */}
        {webcams
          .filter(webcam => markerImages.has(webcam.id)) // Only show markers with loaded images
          .map(webcam => {
            // Find corresponding camera conditions
            const cameraData = cameras.find(cam => 
              cam.id === webcam.id || 
              (Math.abs(cam.lat - webcam.lat) < 0.001 && Math.abs(cam.lon - webcam.lon) < 0.001)
            );
            
            const hasData = !!cameraData;
            const fogScore = cameraData?.fog_score ?? 0;
            
            // Create icon with current image state
            const icon = createMarkerIcon(webcam.id, fogScore, hasData);
            
            return (
              <Marker 
                key={webcam.id}
                position={[webcam.lat, webcam.lon]}
                icon={icon}
                eventHandlers={{
                  click: () => handleMarkerClick(webcam)
                }}
              >
              </Marker>
            );
          })}
      </MapContainer>
      
      {/* Floating Visibility Legend */}
      <div 
        className="absolute bottom-6 left-6 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-4 border border-gray-200"
        style={{ zIndex: 1000 }}
      >
        <h4 className="font-semibold text-gray-800 mb-3 flex items-center text-sm">
          Visibility
          <Link 
            to="/measuring-fog"
            className="ml-2 w-4 h-4 bg-blue-100 text-blue-600 rounded-full text-xs font-bold hover:bg-blue-200 transition-colors inline-flex items-center justify-center"
            title="View fog intensity examples"
          >
            ?
          </Link>
        </h4>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#6c757d' }}></div>
            <span className="text-xs">No Data</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#28a745' }}></div>
            <span className="text-xs">Clear (0-20)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#ffc107' }}></div>
            <span className="text-xs">Light Fog (20-40)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#fd7e14' }}></div>
            <span className="text-xs">Moderate Fog (40-60)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#dc3545' }}></div>
            <span className="text-xs">Heavy Fog (60-80)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: '#6f42c1' }}></div>
            <span className="text-xs">Very Heavy Fog (80+)</span>
          </div>
        </div>
      </div>
      
      {/* Centered Timestamp Indicator */}
      {(() => {
        const { timestamp, color, allSame } = getGlobalTimestamp();
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
      })()}
      
      {/* Bottom Modal */}
      {isModalOpen && selectedWebcam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-[2000] flex items-end">
          <div 
            className="fixed inset-0" 
            onClick={closeModal}
          />
          <div 
            className="bg-white w-full h-3/4 rounded-t-2xl shadow-2xl transform transition-transform duration-300 ease-out relative z-10"
            style={{ animation: 'slideUp 0.3s ease-out' }}
          >
            {/* Header with Fog Conditions, Live Camera, and Close button */}
            <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between">
              {(() => {
                const cameraData = cameras.find(cam => 
                  cam.id === selectedWebcam.id || 
                  (Math.abs(cam.lat - selectedWebcam.lat) < 0.001 && Math.abs(cam.lon - selectedWebcam.lon) < 0.001)
                );
                const fogScore = cameraData?.fog_score ?? 0;
                const fogLevel = cameraData?.fog_level ?? 'No data';
                const confidence = cameraData?.confidence ?? 0;
                
                const getFogBadgeColor = (level: string) => {
                  switch (level.toLowerCase()) {
                    case 'clear': return 'bg-green-100 text-green-800';
                    case 'light fog': return 'bg-yellow-100 text-yellow-800';
                    case 'moderate fog': return 'bg-orange-100 text-orange-800';
                    case 'heavy fog': return 'bg-red-100 text-red-800';
                    case 'very heavy fog': return 'bg-purple-100 text-purple-800';
                    default: return 'bg-gray-100 text-gray-800';
                  }
                };

                return (
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
                );
              })()}
              
              <button
                onClick={closeModal}
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
                    alt={`${selectedWebcam.name} latest view`}
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
                <h2 className="text-2xl font-bold text-gray-800 flex-1 min-w-0">{selectedWebcam.name}</h2>
                {selectedWebcam.video_url && (
                  <a 
                    href={selectedWebcam.video_url} 
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
      )}
      
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
    </div>
  );
};

export default FogMap;