<script lang="ts">
	import { page } from '$app/stores';

	interface Props {
		isOpen: boolean;
		onClose: () => void;
	}

	let { isOpen, onClose }: Props = $props();

	function getMenuItemClass(path: string): string {
		return $page.url.pathname === path
			? 'block text-blue-600 font-medium py-2 px-4 rounded-lg bg-blue-50'
			: 'block text-gray-800 hover:text-blue-600 font-medium py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors';
	}
</script>

{#if isOpen}
	<div class="fixed inset-0" style="z-index: 10000">
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black/50 backdrop-blur-sm"
			role="button"
			tabindex="0"
			onclick={onClose}
			onkeydown={(e) => e.key === 'Escape' && onClose()}
		></div>

		<!-- Sidebar Panel -->
		<div class="absolute top-0 right-0 h-full w-80 bg-white/95 backdrop-blur-md shadow-2xl">
			<div class="p-6 h-full flex flex-col">
				<!-- Close Button -->
				<button
					onclick={onClose}
					class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition-colors"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>

				<!-- Top Section -->
				<div>
					<!-- Title -->
					<div class="mb-8 mt-4">
						<a href="/">
							<h1 class="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent hover:from-blue-700 hover:to-purple-700 transition-all duration-300 cursor-pointer">
								karl cam
							</h1>
							<p class="text-gray-600 mt-2 hover:text-gray-800 transition-colors cursor-pointer">Live San Francisco fog</p>
						</a>
					</div>

					<!-- Main Links -->
					<nav class="space-y-4">
						<a
							href="/measuring-fog"
							class={getMenuItemClass('/measuring-fog')}
						>
							Measuring Fog with Cameras
						</a>
						<a
							href="/why-karlcam"
							class={getMenuItemClass('/why-karlcam')}
						>
							Why KarlCam?
						</a>
						<a
							href="https://x.com/KarlTheFog"
							target="_blank"
							rel="noopener noreferrer"
							class="block text-gray-800 hover:text-blue-600 font-medium py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors"
						>
							Who is Karl the Fog? ↗
						</a>
					</nav>
				</div>

				<!-- Spacer -->
				<div class="flex-1"></div>

				<!-- Bottom Section - About Creator -->
				<div class="border-t border-gray-200 pt-4 mt-4 space-y-2">
					<a
						href="/about"
						class="block text-gray-600 hover:text-blue-600 text-sm py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors"
					>
						How I built this
					</a>
					<a
						href="/about-creator"
						class="block text-gray-600 hover:text-blue-600 text-sm py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors"
					>
						Made by Reed Klaeser
					</a>
				</div>
			</div>
		</div>
	</div>
{/if}
