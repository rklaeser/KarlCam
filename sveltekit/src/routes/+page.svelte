<script lang="ts">
	import { onMount } from 'svelte';
	import { collection, query, where, getDocs } from 'firebase/firestore';
	import { getFirestoreClient } from '$lib/firebase';
	import type { Webcam, CameraLabel } from '$lib/types';
	import FogMap from '$lib/components/FogMap.svelte';
	import CameraModal from '$lib/components/CameraModal.svelte';
	import FogLegend from '$lib/components/FogLegend.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';

	let webcams = $state<Webcam[]>([]);
	let cameraLabels = $state<Map<string, CameraLabel>>(new Map());
	let error = $state<string | null>(null);

	let sidebarOpen = $state(false);
	let selectedWebcam = $state<Webcam | null>(null);
	let isModalOpen = $state(false);

	/**
	 * Load webcams from Firestore
	 */
	async function loadWebcams(): Promise<void> {
		try {
			const db = getFirestoreClient();
			const webcamsRef = collection(db, 'webcams');
			const q = query(webcamsRef, where('active', '==', true));
			const snapshot = await getDocs(q);

			webcams = snapshot.docs.map((doc) => ({
				id: doc.id,
				name: doc.data().name,
				latitude: doc.data().latitude,
				longitude: doc.data().longitude,
				url: doc.data().url,
				active: doc.data().active
			}));

			// Get latest labels for each webcam
			await Promise.all(webcams.map((webcam) => getLatestLabel(webcam.id)));
		} catch (err) {
			console.error('Error loading webcams:', err);
			error = err instanceof Error ? err.message : 'Failed to load webcams';
	}
}

	/**
	 * Get the latest label for a camera from the API
	 * The API will check Firestore first, and if no recent label exists,
	 * it will generate one using Gemini AI
	 */
	async function getLatestLabel(cameraId: string): Promise<void> {
		try {
			console.log(`Fetching label for camera ${cameraId}...`);
			const response = await fetch(`/api/label/${cameraId}`);

			if (!response.ok) {
				console.error(`API error for camera ${cameraId}:`, response.statusText);
				return;
			}

			const data = await response.json();
			console.log(`Received label for camera ${cameraId}:`, data);

			if (data.label) {
				const label: CameraLabel = {
					camera_id: data.label.camera_id,
					camera_name: data.label.camera_name,
					timestamp: new Date(data.label.timestamp),
					image_url: data.label.image_url,
					fog_score: data.label.fog_score,
					fog_level: data.label.fog_level,
					confidence: data.label.confidence,
					reasoning: data.label.reasoning,
					weather_conditions: data.label.weather_conditions,
					latitude: data.label.latitude,
					longitude: data.label.longitude,
					source_environment: data.label.source_environment,
					labeler_name: data.label.labeler_name
				};
				cameraLabels.set(cameraId, label);
				// Trigger Svelte reactivity by reassigning the Map
				cameraLabels = new Map(cameraLabels);
				console.log(`Label set for camera ${cameraId}:`, label.fog_level, label.fog_score);
			}
		} catch (err) {
			console.error(`Error getting label for camera ${cameraId}:`, err);
		}
	}

	function handleMarkerClick(webcam: Webcam) {
		selectedWebcam = webcam;
		isModalOpen = true;
	}

	function closeModal() {
		isModalOpen = false;
		selectedWebcam = null;
	}

	onMount(() => {
		loadWebcams();
	});
</script>

<svelte:head>
	<title>KarlCam - San Francisco Fog Monitor</title>
</svelte:head>

<div class="h-screen bg-gray-100 flex flex-col overflow-hidden">
	<!-- Hamburger Menu Button -->
	<button
		onclick={() => (sidebarOpen = true)}
		class="fixed top-6 right-6 bg-white/90 backdrop-blur-sm text-gray-800 p-3 rounded-full shadow-lg hover:bg-white hover:shadow-xl transition-all duration-300"
		style="z-index: 9999"
	>
		<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M4 6h16M4 12h16M4 18h16" />
		</svg>
	</button>

	<!-- Sidebar -->
	<Sidebar isOpen={sidebarOpen} onClose={() => (sidebarOpen = false)} />

	<!-- Full-width Map -->
	<div class="flex-1 relative">
		<FogMap {webcams} {cameraLabels} onMarkerClick={handleMarkerClick} />

		<!-- Fog Legend Overlay -->
		<FogLegend />

		<!-- Error overlay -->
		{#if error && webcams.length === 0}
			<div class="absolute top-20 left-1/2 transform -translate-x-1/2 z-[10000]">
				<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded shadow-lg">
					{error}
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Camera Modal -->
<CameraModal
	isOpen={isModalOpen}
	webcam={selectedWebcam}
	label={selectedWebcam ? cameraLabels.get(selectedWebcam.id) || null : null}
	onClose={closeModal}
/>
