<script lang="ts">
	import Sidebar from '$lib/components/Sidebar.svelte';

	let sidebarOpen = $state(false);
</script>

<svelte:head>
	<title>How I Built This - KarlCam</title>
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
			<h1 class="text-3xl md:text-4xl font-bold text-gray-800 mb-6">How I Built This</h1>

			<div class="space-y-8">
				<div>
					<h3 class="text-xl font-semibold text-gray-800 mb-4">Architecture Overview</h3>
					<p class="text-gray-700 leading-relaxed">
						KarlCam pulls images from public webcams and scores them for fog using Gemini and in time a <strong>Convolutional Neural Network</strong>. It is built on <strong>Google Cloud Platform</strong> for about $10/month.
					</p>
				</div>

				<div>
					<h3 class="text-xl font-semibold text-gray-800 mb-4">Data Flow</h3>
					<ol class="space-y-4 text-gray-700">
						<li class="flex gap-3">
							<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">1</span>
							<div>
								<strong>Image Collection:</strong> Every half hour a Google Cloud Run job captures images from public webcams around San Francisco and scores them for fog using Gemini.
							</div>
						</li>
						<li class="flex gap-3">
							<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">2</span>
							<div>
								<strong>Cloud Storage and SQL:</strong> Images are stored in Google Cloud Storage buckets and fog scores are stored in a Cloud SQL DB.
							</div>
						</li>
						<li class="flex gap-3">
							<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">3</span>
							<div>
								<strong>Review:</strong> An admin site let's me review the fog scores and correct them if needed.
							</div>
						</li>
						<li class="flex gap-3">
							<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">4</span>
							<div>
								<strong>Model Training:</strong> After enough images are collected from a range of conditions a supervised learning approach will be used to train the Convolutional Neural Network (CNN) and will replace Gemini. This should be cheaper, faster, and more accurate than Gemini but we shall see.
							</div>
						</li>
						<li class="flex gap-3">
							<span class="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">5</span>
							<div>
								<strong>KarlCam Website:</strong> The latest fog scores are displayed here.
							</div>
						</li>
					</ol>
				</div>

				<div>
					<h3 class="text-xl font-semibold text-gray-800 mb-6">Google Cloud Services Used</h3>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						<div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
							<h4 class="font-semibold text-gray-800 mb-2">Cloud Storage</h4>
							<p class="text-sm text-gray-600">Stores webcam images with automatic lifecycle management</p>
						</div>
						<div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
							<h4 class="font-semibold text-gray-800 mb-2">Cloud SQL</h4>
							<p class="text-sm text-gray-600">PostgreSQL database for metadata and analysis results</p>
						</div>
						<div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
							<h4 class="font-semibold text-gray-800 mb-2">Gemini API</h4>
							<p class="text-sm text-gray-600">AI model for initial training data</p>
						</div>
						<div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
							<h4 class="font-semibold text-gray-800 mb-2">Cloud Scheduler</h4>
							<p class="text-sm text-gray-600">Automates image collection every 30 minutes</p>
						</div>
						<div class="bg-gray-50 p-4 rounded-lg border border-gray-200 md:col-span-2 lg:col-span-1">
							<h4 class="font-semibold text-gray-800 mb-2">Cloud Run</h4>
							<p class="text-sm text-gray-600">Containerized deployment with auto-scaling. Cheaper than always on containers in Kubernetes because of low volume.</p>
						</div>
					</div>
				</div>

				<div>
					<h3 class="text-xl font-semibold text-gray-800 mb-4">Coming Soon</h3>
					<ul class="space-y-4 text-gray-700">
						<li class="flex gap-3">
							<span class="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2"></span>
							<div>
								<strong>Train CNN:</strong> Train and deploy the CNN. Will the CNN beat Gemini? Should individual models be trained for each camera location to account for unique viewing angles, lighting conditions, and dirt on the lens.
							</div>
						</li>
						<li class="flex gap-3">
							<span class="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2"></span>
							<div>
								<strong>Add more cameras:</strong> <a href="https://www.windy.com/-Webcams-San-Francisco-Marina-District/webcams/1693167474?37.796,-122.461,12" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">Windy</a> has a list of SF cameras, I'll add a few more outside SF and keep looking for others in SF.
							</div>
						</li>
					</ul>
				</div>

				<div>
					<h3 class="text-xl font-semibold text-gray-800 mb-4">Learn More</h3>
					<ul>
						<li>
							<a
								href="https://github.com/rklaeser/KarlCam"
								target="_blank"
								rel="noopener noreferrer"
								class="inline-flex items-center text-blue-600 hover:text-blue-800 underline font-medium"
							>
								📂 View Source Code on GitHub
							</a>
						</li>
					</ul>
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
