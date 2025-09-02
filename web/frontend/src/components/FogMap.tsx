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
}

const FogMap: React.FC<FogMapProps> = ({ webcams, cameras = [] }) => {
  // Track cameras that have failed to load images
  const [inactiveCameras, setInactiveCameras] = useState<Set<string>>(new Set());
  
  // List of cameras to mark as inactive (you can add more IDs here)
  const knownInactiveCameras = new Set(['ipcamlive']);

  // Set up callback for marking cameras as inactive
  useEffect(() => {
    (window as any).markCameraInactive = (cameraId: string) => {
      setInactiveCameras(prev => new Set(Array.from(prev).concat(cameraId)));
    };
    
    return () => {
      delete (window as any).markCameraInactive;
    };
  }, []);

  const getFogColor = (fogScore: number): string => {
    if (fogScore < 20) return '#28a745'; // Green - Clear
    if (fogScore < 40) return '#ffc107'; // Yellow - Light fog
    if (fogScore < 60) return '#fd7e14'; // Orange - Moderate fog
    if (fogScore < 80) return '#dc3545'; // Red - Heavy fog
    return '#6f42c1'; // Purple - Very heavy fog
  };

  const createCameraImageIcon = (imageUrl: string, fogScore: number, webcamId: string): L.DivIcon => {
    const borderColor = getFogColor(fogScore);
    const size = 80; // Fixed size for camera images
    
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
          src="${imageUrl}" 
          style="
            width: 100%;
            height: 100%;
            object-fit: cover;
          "
          onerror="
            console.log('Map marker image load error for webcam: ${webcamId}');
            const imgElement = this;
            
            // Try to fallback to latest collected image
            fetch('http://localhost:8002/api/public/cameras/${webcamId}/latest-image')
              .then(response => {
                if (!response.ok) {
                  throw new Error('No collected image available');
                }
                return response.json();
              })
              .then(data => {
                console.log('Map marker fallback to collected image:', data);
                const fullImageUrl = 'http://localhost:8002' + data.image_url;
                imgElement.src = fullImageUrl;
                imgElement.style.opacity = '0.8';
              })
              .catch(fallbackError => {
                console.log('Map marker fallback also failed for ${webcamId}:', fallbackError);
                // Mark this camera as inactive
                window.markCameraInactive && window.markCameraInactive('${webcamId}');
                imgElement.style.display='none'; 
                imgElement.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;color:#666;font-size:24px;\\'>📷</div>';
              });
          "
        />
      </div>
    `;

    return L.divIcon({
      html: html,
      className: 'camera-image-marker',
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
      popupAnchor: [0, -(size/2) - 5]
    });
  };

  const createFallbackIcon = (fogScore: number): L.DivIcon => {
    const borderColor = getFogColor(fogScore);
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
        
        {/* Render camera images as markers */}
        {webcams
          .filter(webcam => !knownInactiveCameras.has(webcam.id) && !inactiveCameras.has(webcam.id))
          .map(webcam => {
          // Find corresponding camera conditions
          const cameraData = cameras.find(cam => 
            cam.id === webcam.id || 
            (Math.abs(cam.lat - webcam.lat) < 0.001 && Math.abs(cam.lon - webcam.lon) < 0.001)
          );
          
          const fogScore = cameraData?.fog_score ?? 0;
          const fogLevel = cameraData?.fog_level ?? 'No data';
          const confidence = cameraData?.confidence ?? 0;
          
          // Create the appropriate icon based on image availability
          const icon = webcam.url 
            ? createCameraImageIcon(webcam.url, fogScore, webcam.id)
            : createFallbackIcon(fogScore);
          
          return (
            <Marker 
              key={webcam.id}
              position={[webcam.lat, webcam.lon]}
              icon={icon}
            >
              <Popup className="fog-popup" maxWidth={350}>
                <div className="text-sm">
                  <h3 className="font-semibold text-gray-800 mb-2">{webcam.name}</h3>
                  
                  {/* Camera Image */}
                  {webcam.url && (
                    <div className="mb-3">
                      <img 
                        src={webcam.url} 
                        alt={`${webcam.name} current view`}
                        className="w-full h-48 object-cover rounded-lg"
                        onError={(e) => {
                          console.log('Image load error for:', webcam.name, 'URL:', webcam.url);
                          const imgElement = e.currentTarget;
                          
                          // Check if element is still in DOM
                          if (!imgElement || !imgElement.parentNode) {
                            return;
                          }
                          
                          // Skip fallback for known inactive cameras
                          if (knownInactiveCameras.has(webcam.id) || inactiveCameras.has(webcam.id)) {
                            console.log('Skipping fallback for inactive camera:', webcam.id);
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'w-full h-48 bg-gray-100 rounded-lg flex flex-col items-center justify-center text-gray-500 text-sm p-4';
                            errorDiv.innerHTML = '📷 Camera currently unavailable';
                            imgElement.parentNode.replaceChild(errorDiv, imgElement);
                            return;
                          }
                          
                          // Try to fallback to latest collected image
                          console.log('Attempting fallback for camera:', webcam.id);
                          fetch(`http://localhost:8002/api/public/cameras/${webcam.id}/latest-image`)
                            .then(response => {
                              console.log('Fallback response status:', response.status);
                              if (!response.ok) {
                                throw new Error('No collected image available');
                              }
                              return response.json();
                            })
                            .then(data => {
                              console.log('Fallback to collected image:', data);
                              // Check if element is still in DOM before updating
                              if (imgElement && imgElement.parentNode) {
                                const fullImageUrl = `http://localhost:8002${data.image_url}`;
                                console.log('Setting fallback image URL:', fullImageUrl);
                                imgElement.src = fullImageUrl;
                                imgElement.title = `Latest collected image from ${new Date(data.timestamp).toLocaleString()}`;
                                imgElement.style.opacity = '0.8'; // Visual hint it's a fallback image
                              }
                            })
                            .catch(fallbackError => {
                              console.log('Fallback also failed:', fallbackError);
                              // Mark camera as inactive for future requests
                              setInactiveCameras(prev => new Set(Array.from(prev).concat(webcam.id)));
                              // Check if element is still in DOM before replacing
                              if (imgElement && imgElement.parentNode) {
                                const errorDiv = document.createElement('div');
                                errorDiv.className = 'w-full h-48 bg-gray-100 rounded-lg flex flex-col items-center justify-center text-gray-500 text-sm p-4';
                                const isHttp = webcam.url.startsWith('http://');
                                errorDiv.innerHTML = isHttp 
                                  ? '⚠️ Camera blocked by browser security<br/><small>HTTP images blocked on HTTPS sites</small>'
                                  : '📷 Camera currently unavailable';
                                imgElement.parentNode.replaceChild(errorDiv, imgElement);
                              }
                            });
                        }}
                      />
                    </div>
                  )}
                  
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