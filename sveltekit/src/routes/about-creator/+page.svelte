<script lang="ts">
	import Sidebar from '$lib/components/Sidebar.svelte';

	let sidebarOpen = $state(false);
</script>

<svelte:head>
	<title>About Reed - KarlCam</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col">
	<!-- Hamburger Menu Button -->
	<button
		onclick={() => (sidebarOpen = true)}
		class="fixed top-6 right-6 bg-white/90 backdrop-blur-sm text-gray-800 p-3 rounded-full shadow-lg hover:bg-white hover:shadow-xl transition-all duration-300"
		style="z-index: 9999"
		aria-label="Open menu"
	>
		<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M4 6h16M4 12h16M4 18h16" />
		</svg>
	</button>

	<!-- Sidebar -->
	<Sidebar isOpen={sidebarOpen} onClose={() => (sidebarOpen = false)} />

	<main class="flex-1 container mx-auto px-6 py-8 mt-8">
		<div class="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg">
			<div class="p-6 md:p-10">
				<div class="flex flex-col md:flex-row items-center md:items-start gap-6 md:gap-8">
					<div class="flex-shrink-0">
						<img
							src="/profile.png"
							alt="Reed"
							class="w-24 h-24 md:w-30 md:h-30 rounded-full object-cover border-4 border-blue-500 shadow-lg hover:scale-105 transition-transform duration-300"
						/>
					</div>
					<div class="flex-1 text-center md:text-left">
						<h2 class="text-2xl md:text-3xl font-semibold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
							Hi I'm Reed!
						</h2>
						<p class="text-gray-700 text-lg leading-relaxed mb-6">
							I recently moved to San Francisco just in time for its
							coldest summer since 1965. SF's fog is extremely localized and I wanted a way
							to see where in the city it was sunny since the weather stations were getting it wrong.
							I'm not sure how useful this will be but it was fun to build!
						</p>
						<div class="flex justify-center md:justify-start gap-4">
							<a
								href="https://www.reedklaeser.com/"
								target="_blank"
								rel="noopener noreferrer"
								class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300"
							>
								🌐 reedklaeser.com
							</a>
						</div>
					</div>
				</div>
			</div>
		</div>
	</main>

	<footer class="bg-white/10 backdrop-blur-md border-t border-white/20 text-white py-6">
		<div class="container mx-auto px-6 text-center">
			<p class="text-blue-100">KarlCam - Real-time fog tracking for San Francisco</p>
		</div>
	</footer>
</div>
