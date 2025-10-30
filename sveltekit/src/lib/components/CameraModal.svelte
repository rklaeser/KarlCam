<script lang="ts">
	import { onMount } from 'svelte';
	import type { Webcam, CameraLabel } from '$lib/types';
	import { getFogBadgeColor } from '$lib/utils';

	interface Props {
		isOpen: boolean;
		webcam: Webcam | null;
		label: CameraLabel | null;
		onClose: () => void;
	}

	let { isOpen, webcam, label, onClose }: Props = $props();

	let modalImageUrl = $state<string | null>(null);
	let modalImageLoading = $state(false);

	// Watch for modal open/close
	$effect(() => {
		if (isOpen && webcam) {
			modalImageUrl = null;
			modalImageLoading = true;

			// Use the image URL from the label if available
			if (label?.image_url) {
				modalImageUrl = label.image_url;
				modalImageLoading = false;
			} else if (webcam.url) {
				// Fallback to webcam URL
				modalImageUrl = webcam.url;
				modalImageLoading = false;
			}
		}
	});

	const fogScore = $derived(label?.fog_score ?? 0);
	const fogLevel = $derived(label?.fog_level ?? 'No data');
	const confidence = $derived((label?.confidence ?? 0) * 100);
</script>

{#if isOpen && webcam}
	<div class="fixed inset-0 bg-black bg-opacity-50 z-[2000] flex items-end">
		<div
			class="fixed inset-0"
			role="button"
			tabindex="0"
			onclick={onClose}
			onkeydown={(e) => e.key === 'Escape' && onClose()}
		></div>
		<div
			class="bg-white w-full h-3/4 rounded-t-2xl shadow-2xl transform transition-transform duration-300 ease-out relative z-10"
			style="animation: slideUp 0.3s ease-out"
		>
			<!-- Header with Fog Conditions and Close button -->
			<div class="absolute top-4 left-4 right-4 z-10 flex items-center justify-between">
				<div class="flex items-center gap-3 flex-wrap bg-white/90 backdrop-blur-sm rounded-full px-4 py-2">
					<span class={`px-3 py-1 rounded-full text-sm font-medium ${getFogBadgeColor(fogLevel)}`}>
						{fogLevel}
					</span>
					<span class="text-sm text-gray-600">
						Score: <span class="font-medium text-gray-800">{fogScore.toFixed(1)}/100</span>
					</span>
					<span class="text-sm text-gray-600">
						Confidence: <span class="font-medium text-gray-800">{confidence.toFixed(1)}%</span>
					</span>
				</div>

				<button
					onclick={onClose}
					class="bg-black bg-opacity-20 hover:bg-opacity-40 text-white rounded-full w-8 h-8 flex items-center justify-center transition-all flex-shrink-0"
				>
					✕
				</button>
			</div>

			<!-- Handle bar -->
			<div class="flex justify-center pt-2">
				<div class="w-12 h-1 bg-gray-300 rounded-full"></div>
			</div>

			<div class="p-6 pt-16 h-full overflow-y-auto">
				<!-- Image Section -->
				<div class="mb-6">
					{#if modalImageLoading}
						<div class="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
							<div class="animate-pulse text-gray-500">📷 Loading image...</div>
						</div>
					{:else if modalImageUrl}
						<img
							src={modalImageUrl}
							alt="{webcam.name} latest view"
							class="w-full max-w-3xl mx-auto object-contain rounded-lg shadow-lg bg-gray-50"
							style="max-height: 60vh; min-height: 200px"
						/>
					{:else}
						<div class="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center text-gray-500">
							📷 No recent image available
						</div>
					{/if}
				</div>

				<!-- Content Section -->
				<div class="flex flex-wrap items-start justify-between gap-4">
					<h2 class="text-2xl font-bold text-gray-800 flex-1 min-w-0">{webcam.name}</h2>
					{#if webcam.video_url}
						<a
							href={webcam.video_url}
							target="_blank"
							rel="noopener noreferrer"
							class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 shadow-lg flex-shrink-0"
						>
							📹 Live video
						</a>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<style>
		@keyframes slideUp {
			from {
				transform: translateY(100%);
			}
			to {
				transform: translateY(0);
			}
		}
	</style>
{/if}
