import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// San Francisco map configuration
export const SF_CENTER: [number, number] = [37.7749, -122.4194];
export const SF_BOUNDS: [[number, number], [number, number]] = [
  [37.7, -122.5], // Southwest
  [37.8, -122.35]  // Northeast
];