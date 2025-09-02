import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from 'react-leaflet';
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
  const getFogColor = (fogScore: number): string => {
    if (fogScore < 20) return '#28a745'; // Green - Clear
    if (fogScore < 40) return '#ffc107'; // Yellow - Light fog
    if (fogScore < 60) return '#fd7e14'; // Orange - Moderate fog
    if (fogScore < 80) return '#dc3545'; // Red - Heavy fog
    return '#6f42c1'; // Purple - Very heavy fog
  };

  const getFogRadius = (fogScore: number): number => {
    return Math.max(10, Math.min(50, fogScore / 2)); // Scale between 10-50 pixels
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
        
        {/* Render fog conditions for each webcam */}
        {webcams.map(webcam => {
          // Find corresponding camera conditions
          const cameraData = cameras.find(cam => 
            cam.id === webcam.id || 
            (Math.abs(cam.lat - webcam.lat) < 0.001 && Math.abs(cam.lon - webcam.lon) < 0.001)
          );
          
          const fogScore = cameraData?.fog_score ?? 0;
          const fogLevel = cameraData?.fog_level ?? 'No data';
          const confidence = cameraData?.confidence ?? 0;
          
          return (
            <div key={webcam.id}>
              {/* Fog intensity circle */}
              <CircleMarker
                center={[webcam.lat, webcam.lon]}
                radius={getFogRadius(fogScore)}
                fillColor={getFogColor(fogScore)}
                color={getFogColor(fogScore)}
                weight={2}
                opacity={0.8}
                fillOpacity={0.4}
              >
                <Popup>
                  <div className="text-sm">
                    <h3 className="font-semibold text-gray-800 mb-2">{webcam.name}</h3>
                    <div className="space-y-1 mb-3">
                      <div><strong>Fog Level:</strong> {fogLevel}</div>
                      <div><strong>Fog Score:</strong> {fogScore.toFixed(1)}/100</div>
                      <div><strong>Confidence:</strong> {confidence.toFixed(1)}%</div>
                    </div>
                    <div>
                      <a 
                        href={webcam.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        📹 View Live Camera
                      </a>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
              
              {/* Camera marker */}
              <Marker position={[webcam.lat, webcam.lon]}>
                <Popup>
                  <div className="text-sm">
                    <h3 className="font-semibold text-gray-800 mb-2">{webcam.name}</h3>
                    <p className="mb-3">{webcam.description}</p>
                    <a 
                      href={webcam.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline"
                    >
                      View Live Camera
                    </a>
                  </div>
                </Popup>
              </Marker>
            </div>
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