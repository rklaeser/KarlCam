<script lang="ts">
	import type { PageData } from './$types';
	import type { NetworkingStatus } from '$lib/types';

	let { data }: { data: PageData } = $props();

	// Get status badge color
	function getStatusColor(status: NetworkingStatus): string {
		const colors: Record<NetworkingStatus, string> = {
			'not_started': 'bg-gray-100 text-gray-800',
			'considering': 'bg-yellow-100 text-yellow-800',
			'registered': 'bg-blue-100 text-blue-800',
			'attended': 'bg-green-100 text-green-800'
		};
		return colors[status];
	}
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">Networking Opportunities</h1>
					<p class="text-sm text-gray-600 mt-1">
						{data.conferences.length} opportunities
						{#if data.lastUpdated}
							• Last updated: {data.lastUpdated}
						{/if}
					</p>
				</div>
				<a
					href="/"
					class="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-300"
				>
					← Dashboard
				</a>
			</div>
		</div>
	</div>

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			{#each data.conferences as event}
				<div class="bg-white shadow rounded-lg p-6">
					<div class="flex items-start justify-between mb-3">
						<h3 class="text-lg font-semibold text-gray-900">{event.name}</h3>
						{#if event.attendance?.status}
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(event.attendance.status)}">
								{event.attendance.status}
							</span>
						{/if}
					</div>

					<p class="text-sm text-gray-600 mb-3">{event.what}</p>

					<div class="space-y-2 mb-4">
						{#if event.where}
							<p class="text-sm text-gray-700">📍 {event.where}</p>
						{/if}
						{#if event.when}
							<p class="text-sm text-gray-700">📅 {event.when}</p>
						{/if}
					</div>

					<div class="mb-4">
						<h4 class="text-sm font-medium text-gray-900 mb-1">Why Attend:</h4>
						<p class="text-sm text-gray-700">{event.why}</p>
					</div>

					{#if event.relevanceToCareer}
						<div class="border-t pt-4">
							<h4 class="text-sm font-medium text-gray-900 mb-2">Relevance:</h4>

							{#if event.relevanceToCareer.topics && event.relevanceToCareer.topics.length > 0}
								<div class="mb-2">
									<p class="text-xs text-gray-600 mb-1">Topics:</p>
									<div class="flex flex-wrap gap-1">
										{#each event.relevanceToCareer.topics as topic}
											<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">
												{topic}
											</span>
										{/each}
									</div>
								</div>
							{/if}

							{#if event.relevanceToCareer.potentialConnections && event.relevanceToCareer.potentialConnections.length > 0}
								<div class="mb-2">
									<p class="text-xs text-gray-600 mb-1">Potential Connections:</p>
									<ul class="text-xs text-gray-700 list-disc list-inside">
										{#each event.relevanceToCareer.potentialConnections as connection}
											<li>{connection}</li>
										{/each}
									</ul>
								</div>
							{/if}
						</div>
					{/if}

					{#if event.attendance?.notes}
						<div class="mt-4 p-3 bg-gray-50 rounded">
							<p class="text-sm text-gray-700">{event.attendance.notes}</p>
						</div>
					{/if}
				</div>
			{/each}
		</div>

		{#if data.conferences.length === 0}
			<div class="bg-white shadow rounded-lg p-8 text-center text-gray-500">
				No networking opportunities tracked yet
			</div>
		{/if}
	</main>
</div>
