<script lang="ts">
	import type { PageData } from './$types';
	import type { EngagementStatus } from '$lib/types';

	let { data }: { data: PageData } = $props();

	// Get status badge color
	function getStatusColor(status: EngagementStatus): string {
		const colors: Record<EngagementStatus, string> = {
			'not_started': 'bg-gray-100 text-gray-800',
			'planning': 'bg-yellow-100 text-yellow-800',
			'active': 'bg-green-100 text-green-800',
			'inactive': 'bg-red-100 text-red-800'
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
					<h1 class="text-3xl font-bold text-gray-900">Communities & Ecosystems</h1>
					<p class="text-sm text-gray-600 mt-1">
						{data.communities.length} communities
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
			{#each data.communities as community}
				<div class="bg-white shadow rounded-lg p-6">
					<div class="flex items-start justify-between mb-3">
						<h3 class="text-lg font-semibold text-gray-900">{community.name}</h3>
						{#if community.engagement?.status}
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(community.engagement.status)}">
								{community.engagement.status}
							</span>
						{/if}
					</div>

					<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700 mb-3">
						{community.type}
					</span>

					<p class="text-sm text-gray-600 mb-3">{community.what}</p>

					<div class="space-y-2 mb-4">
						{#if community.where?.physical}
							<p class="text-sm text-gray-700">📍 {community.where.physical}</p>
						{/if}
						{#if community.where?.online}
							<p class="text-sm text-gray-700">💬 {community.where.online}</p>
						{/if}
						{#if community.when}
							<p class="text-sm text-gray-700">📅 {community.when}</p>
						{/if}
					</div>

					<div class="mb-4">
						<h4 class="text-sm font-medium text-gray-900 mb-1">Why Join:</h4>
						<p class="text-sm text-gray-700">{community.why}</p>
					</div>

					{#if community.relevanceToCareer}
						<div class="border-t pt-4">
							<h4 class="text-sm font-medium text-gray-900 mb-1">Relevance to Career:</h4>
							<p class="text-sm text-gray-700">{community.relevanceToCareer}</p>
						</div>
					{/if}

					{#if community.engagement?.plannedProjects && community.engagement.plannedProjects.length > 0}
						<div class="mt-4">
							<h4 class="text-sm font-medium text-gray-900 mb-2">Planned Projects:</h4>
							<ul class="text-sm text-gray-700 list-disc list-inside">
								{#each community.engagement.plannedProjects as project}
									<li>{project}</li>
								{/each}
							</ul>
						</div>
					{/if}

					{#if community.engagement?.notes}
						<div class="mt-4 p-3 bg-gray-50 rounded">
							<p class="text-sm text-gray-700">{community.engagement.notes}</p>
						</div>
					{/if}
				</div>
			{/each}
		</div>

		{#if data.communities.length === 0}
			<div class="bg-white shadow rounded-lg p-8 text-center text-gray-500">
				No communities tracked yet
			</div>
		{/if}
	</main>
</div>
