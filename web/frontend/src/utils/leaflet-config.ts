import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// San Francisco map configuration
export const SF_CENTER: [number, number] = [37.7749, -122.4194];
export const SF_BOUNDS: [[number, number], [number, number]] = [
  [37.7, -122.5], // Southwest
  [37.8, -122.35]  // Northeast
];