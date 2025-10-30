<script lang="ts">
	import type { PageData } from './$types';
	import type { JobInteractionStatus } from '$lib/types';

	let { data }: { data: PageData } = $props();

	let activeTab = $state<'exploring' | 'applying' | 'rejected' | 'declined' | 'reference' | 'past'>('exploring');

	// Filter companies based on active tab
	let filteredCompanies = $derived(() => {
		return data.companies.filter(company => {
			if (!company.jobInteraction) return false;

			const status = company.jobInteraction.status;

			if (activeTab === 'exploring') {
				return ['exploring', 'considering', 'interested', 'not_started'].includes(status);
			} else if (activeTab === 'applying') {
				return ['applying', 'interviewing'].includes(status);
			} else if (activeTab === 'rejected') {
				return status === 'rejected';
			} else if (activeTab === 'declined') {
				return status === 'declined';
			} else if (activeTab === 'reference') {
				return status === 'reference';
			} else if (activeTab === 'past') {
				return status === 'past';
			}
			return false;
		});
	});

	// Get status badge color
	function getStatusColor(status: JobInteractionStatus): string {
		const colors: Record<JobInteractionStatus, string> = {
			'not_started': 'bg-gray-100 text-gray-800',
			'interested': 'bg-yellow-100 text-yellow-800',
			'considering': 'bg-yellow-100 text-yellow-800',
			'exploring': 'bg-yellow-100 text-yellow-800',
			'applying': 'bg-blue-100 text-blue-800',
			'interviewing': 'bg-purple-100 text-purple-800',
			'offer': 'bg-green-100 text-green-800',
			'accepted': 'bg-green-200 text-green-900',
			'declined': 'bg-red-100 text-red-800',
			'rejected': 'bg-gray-200 text-gray-700',
			'reference': 'bg-indigo-100 text-indigo-800',
			'past': 'bg-gray-100 text-gray-600'
		};
		return colors[status] || 'bg-gray-100 text-gray-800';
	}

	// Get fit badge color
	function getFitColor(fit?: 'excellent' | 'good' | 'moderate' | 'poor'): string {
		if (!fit) return 'bg-gray-100 text-gray-600';

		const colors = {
			'excellent': 'bg-green-100 text-green-800',
			'good': 'bg-blue-100 text-blue-800',
			'moderate': 'bg-yellow-100 text-yellow-800',
			'poor': 'bg-red-100 text-red-800'
		};
		return colors[fit];
	}
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">Companies</h1>
					<p class="text-sm text-gray-600 mt-1">
						Tracking {filteredCompanies().length} companies
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

	<!-- Tabs -->
	<div class="bg-white border-b">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<nav class="-mb-px flex space-x-8">
				<button
					onclick={() => (activeTab = 'exploring')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'exploring'}
					class:text-blue-600={activeTab === 'exploring'}
					class:border-transparent={activeTab !== 'exploring'}
					class:text-gray-500={activeTab !== 'exploring'}
				>
					Exploring
				</button>
				<button
					onclick={() => (activeTab = 'applying')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'applying'}
					class:text-blue-600={activeTab === 'applying'}
					class:border-transparent={activeTab !== 'applying'}
					class:text-gray-500={activeTab !== 'applying'}
				>
					Applying
				</button>
				<button
					onclick={() => (activeTab = 'rejected')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'rejected'}
					class:text-blue-600={activeTab === 'rejected'}
					class:border-transparent={activeTab !== 'rejected'}
					class:text-gray-500={activeTab !== 'rejected'}
				>
					Rejected
				</button>
				<button
					onclick={() => (activeTab = 'declined')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'declined'}
					class:text-blue-600={activeTab === 'declined'}
					class:border-transparent={activeTab !== 'declined'}
					class:text-gray-500={activeTab !== 'declined'}
				>
					Declined
				</button>
				<button
					onclick={() => (activeTab = 'reference')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'reference'}
					class:text-blue-600={activeTab === 'reference'}
					class:border-transparent={activeTab !== 'reference'}
					class:text-gray-500={activeTab !== 'reference'}
				>
					Reference
				</button>
				<button
					onclick={() => (activeTab = 'past')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'past'}
					class:text-blue-600={activeTab === 'past'}
					class:border-transparent={activeTab !== 'past'}
					class:text-gray-500={activeTab !== 'past'}
				>
					Past
				</button>
			</nav>
		</div>
	</div>

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="bg-white shadow overflow-hidden rounded-lg">
			<table class="min-w-full divide-y divide-gray-200">
				<thead class="bg-gray-50">
					<tr>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
							Company
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
							Location
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
							Domain Fit
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
							Mission Fit
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
							Status
						</th>
					</tr>
				</thead>
				<tbody class="bg-white divide-y divide-gray-200">
					{#each filteredCompanies() as company}
						<tr class="hover:bg-gray-50">
							<td class="px-6 py-4 whitespace-nowrap">
								<a href="/companies/{company.id}" class="text-blue-600 hover:underline font-medium">
									{company.name}
								</a>
								{#if company.mission}
									<p class="text-xs text-gray-500 mt-1">{company.mission}</p>
								{/if}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
								{company.location}
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								{#if company.fit?.domain}
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getFitColor(company.fit.domain)}">
										{company.fit.domain}
									</span>
								{:else}
									<span class="text-sm text-gray-400">-</span>
								{/if}
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								{#if company.fit?.mission}
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getFitColor(company.fit.mission)}">
										{company.fit.mission}
									</span>
								{:else}
									<span class="text-sm text-gray-400">-</span>
								{/if}
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								{#if company.jobInteraction}
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(company.jobInteraction.status)}">
										{company.jobInteraction.status}
									</span>
								{:else}
									<span class="text-sm text-gray-400">-</span>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>

			{#if filteredCompanies().length === 0}
				<div class="px-6 py-8 text-center text-gray-500">
					No companies found for this filter
				</div>
			{/if}
		</div>
	</main>
</div>
