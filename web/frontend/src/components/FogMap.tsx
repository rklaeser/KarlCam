import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Popup, Marker } from 'react-leaflet';
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
  // Track which camera images have successfully loaded (kept for potential future use)
  const [loadedCameras, setLoadedCameras] = useState<Set<string>>(new Set());
  
  // Set up callback for marking cameras as loaded
  useEffect(() => {
    (window as any).markCameraLoaded = (cameraId: string) => {
      setLoadedCameras(prev => new Set(Array.from(prev).concat(cameraId)));
    };
    
    return () => {
      delete (window as any).markCameraLoaded;
    };
  }, []);

  const getFogColor = (fogScore: number, hasData: boolean = true): string => {
    if (!hasData) return '#6c757d'; // Grey - No data
    if (fogScore < 20) return '#28a745'; // Green - Clear
    if (fogScore < 40) return '#ffc107'; // Yellow - Light fog
    if (fogScore < 60) return '#fd7e14'; // Orange - Moderate fog
    if (fogScore < 80) return '#dc3545'; // Red - Heavy fog
    return '#6f42c1'; // Purple - Very heavy fog
  };

  const createDatabaseImageIcon = (webcamId: string, fogScore: number, hasData: boolean = true): L.DivIcon => {
    const borderColor = getFogColor(fogScore, hasData);
    const size = 80; // Fixed size for camera images
    const databaseImageUrl = `${apiBase}/api/public/cameras/${webcamId}/latest-image`;
    
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
      ">
        <img 
          src="${databaseImageUrl}" 
          style="
            width: 100%;
            height: 100%;
            object-fit: cover;
          "
          onload="
            window.markCameraLoaded && window.markCameraLoaded('${webcamId}');
          "
          onerror="
            console.log('Database image load error for webcam: ${webcamId}');
            this.style.display='none'; 
            this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;color:#666;font-size:24px;\\'>📷</div>';
          "
        />
      </div>
    `;

    return L.divIcon({
      html: html,
      className: 'camera-database-marker',
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
      popupAnchor: [0, -(size/2) - 5]
    });
  };

  const createFallbackIcon = (fogScore: number, hasData: boolean = true): L.DivIcon => {
    const borderColor = getFogColor(fogScore, hasData);
    const size = 80;
    
    const html = `
      <div style="
        width: ${size}px;
        height: ${size}px;
        border: 3px solid ${borderColor};
        border-radius: 50%;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #666;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      ">
        📷
      </div>
    `;

    return L.divIcon({
      html: html,
      className: 'camera-fallback-marker',
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
        
        {/* Render database images as markers */}
        {webcams.map(webcam => {
          // Find corresponding camera conditions
          const cameraData = cameras.find(cam => 
            cam.id === webcam.id || 
            (Math.abs(cam.lat - webcam.lat) < 0.001 && Math.abs(cam.lon - webcam.lon) < 0.001)
          );
          
          const hasData = !!cameraData;
          const fogScore = cameraData?.fog_score ?? 0;
          const fogLevel = cameraData?.fog_level ?? 'No data';
          const confidence = cameraData?.confidence ?? 0;
          
          // Use database image for marker (will fallback to camera icon on error)
          const icon = createDatabaseImageIcon(webcam.id, fogScore, hasData);
          
          return (
            <Marker 
              key={webcam.id}
              position={[webcam.lat, webcam.lon]}
              icon={icon}
            >
              <Popup className="fog-popup" maxWidth={350}>
                <div className="text-sm">
                  <h3 className="font-semibold text-gray-800 mb-2">{webcam.name}</h3>
                  
                  {/* Database Image */}
                  <div className="mb-3">
                    <img 
                      src={`${apiBase}/api/public/cameras/${webcam.id}/latest-image`}
                      alt={`${webcam.name} latest collected view`}
                      className="w-full h-48 object-cover rounded-lg"
                      onError={(e) => {
                        console.log('Database image load error for:', webcam.name);
                        const imgElement = e.currentTarget;
                        
                        if (imgElement && imgElement.parentNode) {
                          const errorDiv = document.createElement('div');
                          errorDiv.className = 'w-full h-48 bg-gray-100 rounded-lg flex flex-col items-center justify-center text-gray-500 text-sm p-4';
                          errorDiv.innerHTML = '📷 No recent image available';
                          imgElement.parentNode.replaceChild(errorDiv, imgElement);
                        }
                      }}
                    />
                  </div>
                  
                  <div className="space-y-1 mb-3">
                    <div><strong>Fog Level:</strong> {fogLevel}</div>
                    <div><strong>Fog Score:</strong> {fogScore.toFixed(1)}/100</div>
                    <div><strong>Confidence:</strong> {confidence.toFixed(1)}%</div>
                  </div>
                  
                  <p className="mb-3">{webcam.description}</p>
                  
                  {webcam.video_url && (
                    <div>
                      <a 
                        href={webcam.video_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        📹 View Live Camera
                      </a>
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
      
      {/* Floating Visibility Legend - overlay on bottom-left of map */}
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
    </div>
  );
};

export default FogMap;