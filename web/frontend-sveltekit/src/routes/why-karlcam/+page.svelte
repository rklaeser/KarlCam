<script lang="ts">
	import Sidebar from '$lib/components/Sidebar.svelte';

	let sidebarOpen = $state(false);
</script>

<svelte:head>
	<title>Why KarlCam? - KarlCam</title>
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
		<div class="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-6 md:p-10">
			<h1 class="text-3xl md:text-4xl font-bold text-gray-800 mb-6">Why KarlCam?</h1>

			<div class="prose prose-lg max-w-none text-gray-600 mb-8">
				<p class="leading-relaxed mb-4">
					I made KarlCam because I wanted to <a href="/about" class="text-blue-600 hover:text-blue-800 underline">learn</a> but also because I found myself cursing the fog and its fickleness and was seeking a better way to avoid it. Here's roughly how it went down:
				</p>

				<div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
					<h3 class="text-lg font-semibold text-gray-800 mb-4">User Story</h3>

					<div class="space-y-3 text-gray-700">
						<p><strong>As a</strong> San Francisco cyclist planning a bike ride,</p>
						<p><strong>I want</strong> to see real-time ground-level fog conditions across different neighborhoods,</p>
						<p><strong>So that</strong> I can choose a route with sun or avoid areas where fog is at ground level.</p>
					</div>

					<div class="mt-4 pt-4 border-t border-blue-200">
						<h4 class="font-semibold text-gray-800 mb-2">Acceptance Criteria:</h4>
						<ul class="space-y-1 text-sm text-gray-700">
							<li>• Weather apps only provide neighborhood-level forecasts without ground-truth data</li>
							<li>• <a href="https://fog.today/" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">fog.today</a> shows satellite view but cannot distinguish clouds from fog. Fog is a cloud at ground level.</li>
							<li>• Need hyperlocal visibility data across San Francisco's varied microclimates</li>
							<li>• Must show current conditions, not just forecasts</li>
						</ul>
					</div>
				</div>

				<div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
					<h3 class="text-lg font-semibold text-gray-800 mb-4">Solution: Real-time SF fog visibility map using public webcam feeds</h3>

					<div class="mb-4">
						<h4 class="font-semibold text-gray-800 mb-2">How it works:</h4>
						<ul class="space-y-1 text-sm text-gray-700">
							<li>• Aggregates public webcams across SF neighborhoods</li>
							<li>• Uses computer vision to detect ground-level fog density</li>
							<li>• Displays color-coded fog conditions on interactive map</li>
							<li>• Updates every 15 minutes</li>
						</ul>
					</div>

					<div class="mb-4">
						<h4 class="font-semibold text-gray-800 mb-2">Key features:</h4>
						<ul class="space-y-1 text-sm text-gray-700">
							<li>• Live visibility status (not forecasts)</li>
							<li>• Neighborhood-level detail for SF microclimates</li>
							<li>• Route planning with fog avoidance</li>
							<li>• Mobile-friendly for checking before/during rides</li>
						</ul>
					</div>

					<p class="text-sm text-gray-700">
						<strong>Delivers:</strong> Ground-truth fog data so cyclists can choose sunny routes and avoid foggy areas
					</p>
				</div>

				<div class="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-6">
					<h4 class="font-semibold text-gray-800 mb-2">But wait... why do we need computer vision?</h4>
					<p class="text-gray-700 mb-3">
						If Reed can see the camera images, what is the value of the computer vision classification of fog density?
					</p>
					<p class="text-gray-700">
						The classification lets Reed scan the map to quickly understand where and how severe the fog is.
						Scanning lots of cameras isn't very easy, but if that's all Reed needed then an existing webcam map like
						<a
							href="https://www.windy.com/-Webcams-San-Francisco-Marina-District/webcams/1693167474?37.807,-122.447,12"
							target="_blank"
							rel="noopener noreferrer"
							class="text-blue-600 hover:text-blue-800 underline"
						>
							Windy
						</a> would meet Reed's need more simply.
					</p>
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
