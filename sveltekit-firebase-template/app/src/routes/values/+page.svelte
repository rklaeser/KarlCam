<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	function getFitColor(score: string): string {
		const colors: Record<string, string> = {
			'excellent': 'border-green-500 bg-green-50',
			'good': 'border-blue-500 bg-blue-50',
			'moderate': 'border-yellow-500 bg-yellow-50',
			'poor': 'border-red-500 bg-red-50'
		};
		return colors[score] || 'border-gray-500 bg-gray-50';
	}
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex justify-between items-start">
				<div>
					<h1 class="text-3xl font-bold text-gray-900 mb-2">Values & Criteria</h1>
					<p class="text-gray-600">{data.description}</p>
					{#if data.lastUpdated}
						<p class="text-sm text-gray-500 mt-1">Last updated: {data.lastUpdated}</p>
					{/if}
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
		<div class="space-y-8">
			<!-- Domain Preferences -->
			<div class="bg-white shadow rounded-lg p-6">
				<h2 class="text-2xl font-semibold mb-4">Domain Preferences</h2>
				<p class="text-gray-600 mb-6">{data.domainPreferences.description}</p>

				<div class="space-y-6">
					{#each ['excellent', 'good', 'moderate', 'poor'] as level}
						{@const category = data.domainPreferences[level]}
						<div class="border-l-4 pl-6 {getFitColor(level)}">
							<h3 class="text-xl font-semibold text-gray-900 mb-2 capitalize">{level}</h3>
							<p class="text-sm text-gray-600 mb-4">{category.criteria}</p>

							<div class="space-y-4">
								{#each category.domains as domain}
									<div class="bg-white rounded-lg p-4 border border-gray-200">
										<h4 class="font-medium text-gray-900 mb-2">{domain.domain}</h4>
										<p class="text-sm text-gray-700 mb-2">{domain.reasoning}</p>

										<div class="flex flex-wrap gap-2 mb-2">
											{#each domain.technicalMethods as method}
												<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800">
													{method}
												</span>
											{/each}
										</div>

										{#if domain.examples.length > 0}
											<p class="text-xs text-gray-500">
												Examples: {domain.examples.join(', ')}
											</p>
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Mission Preferences -->
			<div class="bg-white shadow rounded-lg p-6">
				<h2 class="text-2xl font-semibold mb-4">Mission Preferences</h2>
				<p class="text-gray-600 mb-6">{data.missionPreferences.description}</p>

				<div class="space-y-6">
					{#each ['excellent', 'good', 'moderate', 'poor'] as level}
						{@const category = data.missionPreferences[level]}
						<div class="border-l-4 pl-6 {getFitColor(level)}">
							<h3 class="text-xl font-semibold text-gray-900 mb-2 capitalize">{level}</h3>
							<p class="text-sm text-gray-600 mb-4">{category.criteria}</p>

							<div class="space-y-4">
								{#each category.missions as mission}
									<div class="bg-white rounded-lg p-4 border border-gray-200">
										<h4 class="font-medium text-gray-900 mb-2">{mission.mission}</h4>
										<p class="text-sm text-gray-700 mb-2">{mission.reasoning}</p>

										{#if mission.examples.length > 0}
											<p class="text-xs text-gray-500">
												Examples: {mission.examples.join(', ')}
											</p>
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</main>
</div>
