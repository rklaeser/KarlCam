<script lang="ts">
	import { onMount } from 'svelte';
	import type { Webcam, CameraLabel } from '$lib/types';
	import { getFogColor, SF_CENTER } from '$lib/utils';
	import L from 'leaflet';
	import 'leaflet/dist/leaflet.css';

	interface Props {
		webcams: Webcam[];
		cameraLabels: Map<string, CameraLabel>;
		onMarkerClick: (webcam: Webcam) => void;
	}

	let { webcams, cameraLabels, onMarkerClick }: Props = $props();

	let mapContainer: HTMLDivElement;
	let map: L.Map | null = null;
	let markers: Map<string, L.CircleMarker> = new Map();

	onMount(() => {
		// Initialize map
		map = L.map(mapContainer, {
			center: SF_CENTER,
			zoom: 11,
			zoomControl: true
		});

		// Add tile layer
		L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
		}).addTo(map);

		// Initialize markers
		updateMarkers();

		// Cleanup on unmount
		return () => {
			if (map) {
				map.remove();
				map = null;
			}
		};
	});

	// Update markers when webcams or labels change
	$effect(() => {
		if (map && webcams) {
			updateMarkers();
		}
	});

	function updateMarkers() {
		if (!map) return;

		// Remove old markers
		markers.forEach((marker) => marker.remove());
		markers.clear();

		// Add new markers
		webcams.forEach((webcam) => {
			const label = cameraLabels.get(webcam.id);
			const fogScore = label?.fog_score;
			const color = getFogColor(fogScore);

			const marker = L.circleMarker([webcam.latitude, webcam.longitude], {
				radius: 12,
				fillColor: color,
				color: '#fff',
				weight: 2,
				opacity: 1,
				fillOpacity: 0.8
			});

			// Add popup
			const popupContent = `
				<div class="text-center">
					<strong>${webcam.name}</strong>
					${
						label
							? `
						<br />
						<span style="color: ${color}">
							${label.fog_level || 'Unknown'} (${fogScore?.toFixed(1) || 'N/A'})
						</span>
					`
							: '<br /><span class="text-gray-500">No data</span>'
					}
				</div>
			`;

			marker.bindPopup(popupContent);

			// Handle click
			marker.on('click', () => {
				onMarkerClick(webcam);
			});

			marker.addTo(map!);
			markers.set(webcam.id, marker);
		});
	}
</script>

<div bind:this={mapContainer} class="w-full h-full"></div>

<style>
	:global(.leaflet-container) {
		font-family: inherit;
	}
</style>
