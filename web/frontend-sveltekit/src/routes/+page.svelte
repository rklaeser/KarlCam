<script lang="ts">
	import { onMount } from 'svelte';
	import { collection, query, where, getDocs, orderBy, limit } from 'firebase/firestore';
	import { getFirestoreClient } from '$lib/firebase';
	import type { Webcam, CameraLabel } from '$lib/types';
	import FogMap from '$lib/components/FogMap.svelte';
	import CameraModal from '$lib/components/CameraModal.svelte';
	import FogLegend from '$lib/components/FogLegend.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';

	let webcams = $state<Webcam[]>([]);
	let cameraLabels = $state<Map<string, CameraLabel>>(new Map());
	let loading = $state(true);
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
		} finally {
			loading = false;
		}
	}

	/**
	 * Get the latest label for a camera from Firestore
	 */
	async function getLatestLabel(cameraId: string): Promise<void> {
		try {
			const db = getFirestoreClient();
			const labelsRef = collection(db, 'labels');
			const cutoffTime = new Date(Date.now() - 30 * 60 * 1000);

			const q = query(
				labelsRef,
				where('camera_id', '==', cameraId),
				where('timestamp', '>=', cutoffTime),
				orderBy('timestamp', 'desc'),
				limit(1)
			);

			const snapshot = await getDocs(q);

			if (!snapshot.empty) {
				const data = snapshot.docs[0].data();
				const label: CameraLabel = {
					camera_id: data.camera_id,
					camera_name: data.camera_name,
					timestamp: data.timestamp.toDate(),
					image_url: data.image_url,
					fog_score: data.fog_score,
					fog_level: data.fog_level,
					confidence: data.confidence,
					reasoning: data.reasoning,
					weather_conditions: data.weather_conditions,
					latitude: data.latitude,
					longitude: data.longitude,
					source_environment: data.source_environment,
					labeler_name: data.labeler_name
				};
				cameraLabels.set(cameraId, label);
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

<div class="h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col overflow-hidden">
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
		{#if loading}
			<div class="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
				<div class="text-white text-center">
					<div class="text-2xl mb-2">Loading cameras...</div>
				</div>
			</div>
		{:else if error && webcams.length === 0}
			<div class="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
				<div class="max-w-md mx-4">
					<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
						{error}
					</div>
				</div>
			</div>
		{:else}
			<FogMap {webcams} {cameraLabels} onMarkerClick={handleMarkerClick} />

			<!-- Fog Legend Overlay -->
			<FogLegend />
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
