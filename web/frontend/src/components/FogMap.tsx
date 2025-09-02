import React, { useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import FogIntensityModal from './FogIntensityModal';

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
  const [showModal, setShowModal] = useState(false);
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
    <div className="fog-map">
      <MapContainer
        center={center}
        zoom={12}
        style={{ height: '400px', width: '100%' }}
        bounds={bounds}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
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
                  <div className="fog-popup">
                    <h3>{webcam.name}</h3>
                    <div className="fog-details">
                      <div><strong>Fog Level:</strong> {fogLevel}</div>
                      <div><strong>Fog Score:</strong> {fogScore.toFixed(1)}/100</div>
                      <div><strong>Confidence:</strong> {confidence.toFixed(1)}%</div>
                    </div>
                    <div className="webcam-link">
                      <a href={webcam.url} target="_blank" rel="noopener noreferrer">
                        📹 View Live Camera
                      </a>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
              
              {/* Camera marker */}
              <Marker position={[webcam.lat, webcam.lon]}>
                <Popup>
                  <div className="webcam-popup">
                    <h3>{webcam.name}</h3>
                    <p>{webcam.description}</p>
                    <a href={webcam.url} target="_blank" rel="noopener noreferrer">
                      View Live Camera
                    </a>
                  </div>
                </Popup>
              </Marker>
            </div>
          );
        })}
      </MapContainer>
      
      {/* Map Legend */}
      <div className="map-legend">
        <h4>
          Fog Intensity
          <button 
            className="help-icon" 
            onClick={() => setShowModal(true)}
            title="View fog intensity examples"
            style={{
              marginLeft: '8px',
              background: 'none',
              border: '1px solid #667eea',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              color: '#667eea',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 'bold',
              padding: '0',
              lineHeight: '1',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#667eea';
              e.currentTarget.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#667eea';
            }}
          >
            ?
          </button>
        </h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#28a745' }}></div>
            <span>Clear (0-20)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#ffc107' }}></div>
            <span>Light Fog (20-40)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#fd7e14' }}></div>
            <span>Moderate Fog (40-60)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#dc3545' }}></div>
            <span>Heavy Fog (60-80)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#6f42c1' }}></div>
            <span>Very Heavy Fog (80+)</span>
          </div>
        </div>
      </div>
      
      {/* Fog Intensity Modal */}
      <FogIntensityModal 
        isOpen={showModal} 
        onClose={() => setShowModal(false)} 
      />
    </div>
  );
};

export default FogMap;