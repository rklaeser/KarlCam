<script lang="ts">
	import Sidebar from '$lib/components/Sidebar.svelte';

	let sidebarOpen = $state(false);

	const fogLevels = [
		{
			level: 'Clear',
			range: '0-20',
			color: '#28a745',
			description: 'No fog visible, clear visibility'
		},
		{
			level: 'Light Fog',
			range: '20-40',
			color: '#ffc107',
			description: 'Slight haze, visibility slightly reduced'
		},
		{
			level: 'Moderate Fog',
			range: '40-60',
			color: '#fd7e14',
			description: 'Noticeable fog, landmarks partially obscured'
		},
		{
			level: 'Heavy Fog',
			range: '60-80',
			color: '#dc3545',
			description: 'Dense fog, visibility significantly reduced'
		},
		{
			level: 'Very Heavy Fog',
			range: '80+',
			color: '#6f42c1',
			description: 'Extremely dense fog, minimal visibility'
		}
	];
</script>

<svelte:head>
	<title>Measuring Fog with Cameras - KarlCam</title>
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
			<h1 class="text-3xl md:text-4xl font-bold text-gray-800 mb-2">Measuring Fog with Cameras</h1>

			<div class="flex items-center gap-2 text-sm text-gray-500 mb-6">
				<span>By Reed Klaeser</span>
				<span>•</span>
				<span>August 28, 2025</span>
				<span>•</span>
				<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
					In Progress
				</span>
			</div>

			<div class="prose prose-lg max-w-none text-gray-600 mb-8">
				<p class="leading-relaxed mb-4">
					Even on the foggiest day of this historically cold San Francisco summer, the familiar sound of Waymos can be heard buzzing along the streets.
					How do they manage in the fog? <a href="https://waymo.com/blog/2021/11/a-fog-blog" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">With radar sensors that can see through it</a>.
					Cameras can't do that, which is why, it's no small controversy that Tesla has rejected radar in favor of cameras (which are cheaper) for its self driving solution.
				</p>

				<div class="my-6 flex justify-center">
					<img
						src="/waymo.webp"
						alt="Waymo vehicle in San Francisco fog"
						class="rounded-lg shadow-lg max-w-full h-auto"
						style="max-height: 400px"
					/>
				</div>

				<p class="leading-relaxed mb-4">
					Tesla thinks they can make up the difference with software. karl.cam attempts the same.
					In a space where the state of the art uses lasers, karl.cam, like Tesla, leans on cameras because
					they are more convenient. Specifically because publicly available webcams are everywhere, making them perfect for local fog measurement. My focus at first
					will be on building karl.cam in Google Cloud and will therefore start by offloading the entire question of fog measurement to an LLM.
					But once the karl.cam system is up and running, I hope to use it to teach myself more mature image analysis approaches. Here's how I'm approaching the problem at the start.
				</p>

				<div class="bg-gray-50 border-l-4 border-gray-500 p-4 mb-6">
					<p class="text-gray-800 font-semibold mb-1">Problem Statement:</p>
					<p class="text-gray-700">Determine the visibility level in a set of fixed images over time.</p>
				</div>

				<h3 class="text-xl font-semibold text-gray-800 mb-4">Approaches</h3>
				<p class="text-gray-600 mb-4">Ordered by increasing complexity</p>

				<ol class="space-y-3 text-gray-700">
					<li class="flex gap-3">
						<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">1</span>
						<div>
							<strong>Ask LLM how foggy it is in a picture</strong>
							<span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Current</span>
						</div>
					</li>
					<li class="flex gap-3">
						<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">2</span>
						<div>
							<strong>Same but also give LLM a clear picture for reference</strong>
							<span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">Next</span>
						</div>
					</li>
					<li class="flex gap-3">
						<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">3</span>
						<div>
							<strong>Collect images, score them with LLM, review and correct them</strong>
							<span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">In Progress</span>
							<p class="text-sm text-gray-600 mt-1">See <a href="https://admin.karl.cam" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">admin.karl.cam</a></p>
						</div>
					</li>
				</ol>
			</div>

			<h2 class="text-2xl font-semibold text-gray-800 mb-6">Fog Intensity Levels</h2>
			<p class="leading-relaxed mb-4 text-gray-600">The farther in meters the visibility is, the lower the intensity level. I am considering switching to meters of visibility directly.</p>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
				{#each fogLevels as level}
					<div class="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
						<div class="p-4 bg-gray-50">
							<div class="flex items-center gap-3 mb-2">
								<div
									class="px-3 py-1 rounded-full text-white text-sm font-semibold"
									style="background-color: {level.color}"
								>
									{level.range}
								</div>
								<h3 class="text-lg font-semibold text-gray-800">{level.level}</h3>
							</div>
						</div>

						<div class="p-4">
							<div class="aspect-video bg-gray-100 rounded-lg border-2 border-dashed flex flex-col items-center justify-center mb-4" style="border-color: {level.color}">
								<div class="text-4xl mb-2">🌫️</div>
								<div class="text-center">
									<div class="text-sm font-medium text-gray-600">Example Image</div>
									<div class="text-xs text-gray-500">{level.level}</div>
								</div>
							</div>

							<p class="text-sm text-gray-600 leading-relaxed">{level.description}</p>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</main>

	<footer class="bg-white/10 backdrop-blur-md border-t border-white/20 text-white py-6">
		<div class="container mx-auto px-6 text-center">
			<p class="text-blue-100">KarlCam - Real-time fog tracking for San Francisco</p>
		</div>
	</footer>
</div>
