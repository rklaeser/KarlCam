<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import type { Webcam, CameraLabel } from '$lib/types';
	import { getFogColor, SF_CENTER } from '$lib/utils';

	interface Props {
		webcams: Webcam[];
		cameraLabels: Map<string, CameraLabel>;
		onMarkerClick: (webcam: Webcam) => void;
	}

	let { webcams, cameraLabels, onMarkerClick }: Props = $props();

	let mapContainer: HTMLDivElement;
	let map: any = null;
	let markers: Map<string, any> = new Map();
	let L: any = null;

	onMount(async () => {
		// Only import Leaflet on the client side
		if (browser) {
			// @ts-ignore
			L = (await import('leaflet')).default;
			// Import CSS
			await import('leaflet/dist/leaflet.css');

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
		}

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
		// Access cameraLabels directly to ensure it's tracked as a dependency
		const labels = cameraLabels;
		if (map && webcams && L) {
			updateMarkers();
		}
	});

	function updateMarkers() {
		if (!map || !L) return;

		// Remove old markers
		markers.forEach((marker) => marker.remove());
		markers.clear();

		// Add markers for webcams with label data (they appear progressively as API calls complete)
		webcams.forEach((webcam) => {
			const label = cameraLabels.get(webcam.id);

			// Skip webcams without label data yet
			if (!label) {
				return;
			}

			const fogScore = label.fog_score;
			const color = getFogColor(fogScore);
			const imageUrl = label.image_url || webcam.url;

			// Create custom HTML marker with camera image inside circle
			const iconHtml = `
				<div style="
					width: 80px;
					height: 80px;
					border-radius: 50%;
					border: 4px solid ${color};
					overflow: hidden;
					background: white;
					box-shadow: 0 2px 8px rgba(0,0,0,0.3);
					cursor: pointer;
				">
					<img
						src="${imageUrl}"
						alt="${webcam.name}"
						style="
							width: 100%;
							height: 100%;
							object-fit: cover;
						"
						onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;color:#666;font-size:24px;\\'>📷</div>';"
					/>
				</div>
			`;

			const customIcon = L.divIcon({
				html: iconHtml,
				className: 'custom-camera-marker',
				iconSize: [80, 80],
				iconAnchor: [40, 40]
			});

			const marker = L.marker([webcam.latitude, webcam.longitude], {
				icon: customIcon
			});

			// Add popup
			const popupContent = `
				<div class="text-center">
					<strong>${webcam.name}</strong>
					<br />
					<span style="color: ${color}">
						${label.fog_level} (${fogScore.toFixed(1)})
					</span>
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

	:global(.custom-camera-marker) {
		background: transparent !important;
		border: none !important;
	}
</style>
